import 'package:flutter/material.dart';
import 'vehicle_catalog.dart';

void main() => runApp(const DiagnosticApp());

class DiagnosticApp extends StatelessWidget {
  const DiagnosticApp({super.key});
  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'AI Auto Diagnostic',
    theme: ThemeData(useMaterial3: true, brightness: Brightness.dark),
    home: const VehicleSetupPage(),
  );
}

class VehicleSetupPage extends StatefulWidget {
  const VehicleSetupPage({super.key});
  @override State<VehicleSetupPage> createState() => _VehicleSetupPageState();
}

class _VehicleSetupPageState extends State<VehicleSetupPage> {
  String make = vehicleCatalog.first.name;
  String model = vehicleCatalog.first.models.first.name;
  String chassis = vehicleCatalog.first.models.first.chassisOptions.first.chassis;
  int year = vehicleCatalog.first.models.first.chassisOptions.first.years.first;
  String engine = vehicleCatalog.first.models.first.chassisOptions.first.engines.first.name;
  String ecu = vehicleCatalog.first.models.first.chassisOptions.first.engines.first.ecus.first;
  bool petrol = true, lpg = false;

  VehicleModelOption get modelData => findModel(make, model) ?? vehicleCatalog.first.models.first;
  VehicleChassisOption get chassisData => findChassis(make, model, chassis) ?? modelData.chassisOptions.first;

  void selectMake(String value) {
    final m=findMake(value)??vehicleCatalog.first; final mo=m.models.first; final ch=mo.chassisOptions.first; final en=ch.engines.first;
    setState(() { make=m.name; model=mo.name; chassis=ch.chassis; year=ch.years.first; engine=en.name; ecu=en.ecus.first; });
  }
  void selectModel(String value) {
    final mo=findModel(make,value)??modelData; final ch=mo.chassisOptions.first; final en=ch.engines.first;
    setState(() { model=mo.name; chassis=ch.chassis; year=ch.years.first; engine=en.name; ecu=en.ecus.first; });
  }
  void selectChassis(String value) {
    final ch=findChassis(make,model,value)??chassisData; final en=ch.engines.first;
    setState(() { chassis=ch.chassis; year=ch.years.first; engine=en.name; ecu=en.ecus.first; });
  }
  void selectEngine(String value) {
    final en=chassisData.engines.firstWhere((e)=>e.name==value,orElse:()=>chassisData.engines.first);
    setState(() { engine=en.name; ecu=en.ecus.first; });
  }

  Widget field(String label,String value,List<String> options,ValueChanged<String> onChanged)=>DropdownButtonFormField<String>(
    value:options.contains(value)?value:null,
    decoration:InputDecoration(labelText:label),
    items:options.map((x)=>DropdownMenuItem(value:x,child:Text(x))).toList(),
    onChanged:(v){if(v!=null)onChanged(v);},
  );

  @override
  Widget build(BuildContext context) {
    final models=findMake(make)?.models.map((x)=>x.name).toList()??[];
    final chassisOptions=modelData.chassisOptions.map((x)=>x.chassis).toList();
    final years=chassisData.years;
    final engines=chassisData.engines.map((x)=>x.name).toList();
    final fuel=<String>[if(petrol)'petrol',if(lpg)'LPG'];
    return Scaffold(
      appBar: AppBar(title: const Text('AI Auto Diagnostic')),
      body: ListView(padding: const EdgeInsets.all(20),children:[
        const Text('Vehicle',style:TextStyle(fontSize:24,fontWeight:FontWeight.w700)),
        const SizedBox(height:8),
        const Text('Select the real-world vehicle identity before starting diagnosis.'),
        const SizedBox(height:20),
        field('Make',make,vehicleCatalog.map((x)=>x.name).toList(),selectMake),
        const SizedBox(height:12),
        field('Model',model,models,selectModel),
        const SizedBox(height:12),
        field('Chassis',chassis,chassisOptions,selectChassis),
        const SizedBox(height:12),
        DropdownButtonFormField<int>(
          value:years.contains(year)?year:years.first,
          decoration:const InputDecoration(labelText:'Year'),
          items:years.map((x)=>DropdownMenuItem(value:x,child:Text('$x'))).toList(),
          onChanged:(v){if(v!=null)setState(()=>year=v);},
        ),
        const SizedBox(height:12),
        field('Engine',engine,engines,selectEngine),
        const SizedBox(height:12),
        TextFormField(key:ValueKey(ecu),initialValue:ecu,readOnly:true,decoration:const InputDecoration(labelText:'ECU')),
        const SizedBox(height:12),
        const Text('Fuel'),
        CheckboxListTile(value:petrol,onChanged:(v)=>setState(()=>petrol=v??false),title:const Text('Petrol'),contentPadding:EdgeInsets.zero),
        CheckboxListTile(value:lpg,onChanged:(v)=>setState(()=>lpg=v??false),title:const Text('LPG'),contentPadding:EdgeInsets.zero),
        const SizedBox(height:12),
        FilledButton.icon(
          onPressed:fuel.isEmpty?null:(){ScaffoldMessenger.of(context).showSnackBar(SnackBar(content:Text('$make $model / $chassis / $year / $engine / $ecu')));},
          icon:const Icon(Icons.play_arrow),label:const Text('Start Diagnostic Session'),
        ),
      ]),
    );
  }
}
