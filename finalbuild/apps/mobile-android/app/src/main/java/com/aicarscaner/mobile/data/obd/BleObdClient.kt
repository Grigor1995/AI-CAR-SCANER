package com.aicarscaner.mobile.data.obd

import android.annotation.SuppressLint
import android.bluetooth.*
import android.bluetooth.le.ScanCallback
import android.bluetooth.le.ScanResult
import android.content.Context
import android.os.Build
import kotlinx.coroutines.*
import kotlinx.coroutines.sync.Mutex
import kotlinx.coroutines.sync.withLock
import java.io.ByteArrayOutputStream
import java.io.IOException
import java.util.UUID
import java.util.concurrent.ConcurrentHashMap
import kotlin.coroutines.resume
import kotlin.coroutines.resumeWithException

/** GATT byte transport only; Backend owns OBD commands, PID support and decoding. */
@SuppressLint("MissingPermission")
class BleObdClient {
    private val connectionState=kotlinx.coroutines.flow.MutableStateFlow(false)
    val connected:kotlinx.coroutines.flow.StateFlow<Boolean> = connectionState
    val isConnected:Boolean get()=connectionState.value
    private var gatt:BluetoothGatt?=null
    private var writer:BluetoothGattCharacteristic?=null
    private var readerID:UUID?=null
    private val lock=Any()
    private val requests=Mutex()
    private var connecting:CancellableContinuation<Unit>?=null
    private var response:CancellableContinuation<String>?=null
    private val bytes=ByteArrayOutputStream()
    private val profiles=mapOf(
        uuid("FFE0") to (uuid("FFE1") to uuid("FFE1")),
        uuid("FFF0") to (uuid("FFF2") to uuid("FFF1")),
        uuid("6E400001-B5A3-F393-E0A9-E50E24DCCA9E") to (uuid("6E400002-B5A3-F393-E0A9-E50E24DCCA9E") to uuid("6E400003-B5A3-F393-E0A9-E50E24DCCA9E"))
    )
    private fun uuid(value:String)=UUID.fromString(if(value.length==4) "0000$value-0000-1000-8000-00805f9b34fb" else value)
    suspend fun scan(context:Context):List<BluetoothDevice> = withContext(Dispatchers.Main) {
        val scanner=context.getSystemService(BluetoothManager::class.java)?.adapter?.bluetoothLeScanner ?: error("Bluetooth unavailable")
        val found=ConcurrentHashMap<String,BluetoothDevice>()
        var failure:Int?=null
        val callback=object:ScanCallback() {
            override fun onScanResult(type:Int,result:ScanResult) {found[result.device.address]=result.device}
            override fun onScanFailed(code:Int) {failure=code}
        }
        scanner.startScan(callback)
        try {delay(5000)} finally {scanner.stopScan(callback)}
        failure?.let {throw IOException("BLE scan failed: $it")}
        found.values.sortedBy {it.name ?: it.address}
    }
    suspend fun connect(context:Context,device:BluetoothDevice):Result<String> = requests.withLock {
        try {
            close()
            withTimeout(15_000) {
                suspendCancellableCoroutine<Unit> { continuation ->
                    synchronized(lock) {connecting=continuation}
                    continuation.invokeOnCancellation {close()}
                    gatt=device.connectGatt(context.applicationContext,false,callback,BluetoothDevice.TRANSPORT_LE)
                    if(gatt==null) close()
                }
            }
            Result.success("Connected")
        } catch(error:TimeoutCancellationException) {close();Result.failure(IOException("BLE connection timed out",error))}
        catch(cancelled:CancellationException) {close();throw cancelled}
        catch(error:Exception) {close();Result.failure(error)}
    }
    private val callback=object:BluetoothGattCallback() {
        override fun onConnectionStateChange(g:BluetoothGatt,status:Int,state:Int) {
            if(g !== gatt) return
            if(status!=BluetoothGatt.GATT_SUCCESS || state==BluetoothProfile.STATE_DISCONNECTED) {close();return}
            if(state==BluetoothProfile.STATE_CONNECTED && !g.discoverServices()) close()
        }
        override fun onServicesDiscovered(g:BluetoothGatt,status:Int) {
            if(g !== gatt) return
            if(status!=BluetoothGatt.GATT_SUCCESS) {close();return}
            val service=g.services.firstOrNull {it.uuid in profiles} ?: run {fail(IOException("Unsupported BLE UART profile"));return}
            val (writeID,readID)=profiles.getValue(service.uuid)
            val write=service.getCharacteristic(writeID)
            val read=service.getCharacteristic(readID)
            val writeFlags=BluetoothGattCharacteristic.PROPERTY_WRITE or BluetoothGattCharacteristic.PROPERTY_WRITE_NO_RESPONSE
            val notifyFlags=BluetoothGattCharacteristic.PROPERTY_NOTIFY or BluetoothGattCharacteristic.PROPERTY_INDICATE
            if(write==null || read==null || write.properties and writeFlags==0 || read.properties and notifyFlags==0) {fail(IOException("Unsupported BLE UART profile"));return}
            writer=write;readerID=read.uuid
            val descriptor=read.getDescriptor(uuid("2902")) ?: run {fail(IOException("BLE notification descriptor missing"));return}
            if(!g.setCharacteristicNotification(read,true)) {close();return}
            val value=if(read.properties and BluetoothGattCharacteristic.PROPERTY_NOTIFY!=0) BluetoothGattDescriptor.ENABLE_NOTIFICATION_VALUE else BluetoothGattDescriptor.ENABLE_INDICATION_VALUE
            val started=if(Build.VERSION.SDK_INT>=33) g.writeDescriptor(descriptor,value)==BluetoothStatusCodes.SUCCESS
            else { @Suppress("DEPRECATION") descriptor.value=value; @Suppress("DEPRECATION") g.writeDescriptor(descriptor) }
            if(!started) close()
        }
        override fun onDescriptorWrite(g:BluetoothGatt,d:BluetoothGattDescriptor,status:Int) {
            if(g !== gatt) return
            if(status!=BluetoothGatt.GATT_SUCCESS) {close();return}
            connectionState.value=true
            val wait=synchronized(lock) {connecting.also {connecting=null}}
            if(wait?.isActive==true) wait.resume(Unit)
        }
        override fun onCharacteristicWrite(g:BluetoothGatt,c:BluetoothGattCharacteristic,status:Int) {if(g===gatt && status!=BluetoothGatt.GATT_SUCCESS) fail(IOException("BLE write failed: $status"))}
        override fun onCharacteristicChanged(g:BluetoothGatt,c:BluetoothGattCharacteristic,value:ByteArray) {if(g===gatt && c.uuid==readerID) received(value)}
        @Deprecated("Used below API 33")
        override fun onCharacteristicChanged(g:BluetoothGatt,c:BluetoothGattCharacteristic) {if(g===gatt && c.uuid==readerID) {@Suppress("DEPRECATION") val value=c.value;if(value!=null) received(value)}}
    }
    private fun received(value:ByteArray) {
        var completion:Pair<CancellableContinuation<String>,String>?=null
        var oversized=false
        synchronized(lock) {
            val wait=response ?: return
            bytes.write(value)
            if(bytes.size()>16384) oversized=true
            else {
                val frame=bytes.toByteArray();val end=frame.indexOf(62.toByte())
                if(end>=0) {response=null;completion=wait to String(frame,0,end,Charsets.US_ASCII);bytes.reset()}
            }
        }
        if(oversized) fail(IOException("OBD response exceeded the transport limit"))
        completion?.let {(wait,text)->if(wait.isActive) wait.resume(text)}
    }
    suspend fun command(command:String,timeoutMs:Long=35_000):Result<String> = requests.withLock {
        try {
            val g=gatt ?: error("BLE adapter disconnected")
            val c=writer ?: error("BLE adapter disconnected")
            check(isConnected) {"BLE adapter disconnected"}
            require(command.length<=16 && !command.contains('\r') && !command.contains('\n')) {"Invalid OBD command"}
            val result=withTimeout(timeoutMs) {
                suspendCancellableCoroutine<String> {wait ->
                    synchronized(lock) {response=wait;bytes.reset()}
                    wait.invokeOnCancellation {close()}
                    val data=(command+"\r").toByteArray(Charsets.US_ASCII)
                    val type=if(c.properties and BluetoothGattCharacteristic.PROPERTY_WRITE!=0) BluetoothGattCharacteristic.WRITE_TYPE_DEFAULT else BluetoothGattCharacteristic.WRITE_TYPE_NO_RESPONSE
                    val started=if(Build.VERSION.SDK_INT>=33) g.writeCharacteristic(c,data,type)==BluetoothStatusCodes.SUCCESS
                    else {@Suppress("DEPRECATION") c.value=data;c.writeType=type;@Suppress("DEPRECATION") g.writeCharacteristic(c)}
                    if(!started) fail(IOException("BLE write could not start"))
                }
            }
            Result.success(result)
        } catch(error:TimeoutCancellationException) {close();Result.failure(IOException("BLE adapter timed out",error))}
        catch(cancelled:CancellationException) {close();throw cancelled}
        catch(error:Exception) {close();Result.failure(error)}
    }
    private fun fail(error:Exception) {
        val pending=synchronized(lock) {
            connectionState.value=false;writer=null;readerID=null;bytes.reset()
            val waits=connecting to response;connecting=null;response=null;waits
        }
        val old=gatt;gatt=null;runCatching {old?.disconnect()};runCatching {old?.close()}
        pending.first?.let {if(it.isActive) it.resumeWithException(error)}
        pending.second?.let {if(it.isActive) it.resumeWithException(error)}
    }
    fun close() {fail(IOException("BLE adapter disconnected"))}
}
