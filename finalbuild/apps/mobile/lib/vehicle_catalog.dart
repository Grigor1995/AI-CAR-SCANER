class VehicleEngineOption {
  const VehicleEngineOption(this.name, this.ecus);
  final String name;
  final List<String> ecus;
}

class VehicleChassisOption {
  const VehicleChassisOption(this.chassis, this.years, this.engines);
  final String chassis;
  final List<int> years;
  final List<VehicleEngineOption> engines;
}

class VehicleModelOption {
  const VehicleModelOption(this.name, this.chassisOptions);
  final String name;
  final List<VehicleChassisOption> chassisOptions;
}

class VehicleMakeOption {
  const VehicleMakeOption(this.name, this.models);
  final String name;
  final List<VehicleModelOption> models;
}

const vehicleCatalog = <VehicleMakeOption>[
  VehicleMakeOption('Mercedes-Benz', [
    VehicleModelOption('E-Class', [
      VehicleChassisOption('W211', [2002,2003,2004,2005,2006,2007,2008,2009], [
        VehicleEngineOption('M112 E32 3.2', ['ME2.8']),
        VehicleEngineOption('M113 E50 5.0', ['ME2.8']),
        VehicleEngineOption('M272 E35 3.5', ['ME9.7']),
        VehicleEngineOption('OM642 3.0 V6', ['CDI']),
      ]),
    ]),
    VehicleModelOption('C-Class', [
      VehicleChassisOption('W204', [2007,2008,2009,2010,2011,2012,2013,2014], [
        VehicleEngineOption('M271 1.8', ['ME9.7']),
        VehicleEngineOption('M272 3.5 V6', ['ME9.7']),
        VehicleEngineOption('OM651 2.1', ['CDI']),
      ]),
    ]),
    VehicleModelOption('E-Class', [
      VehicleChassisOption('W212', [2009,2010,2011,2012,2013,2014,2015,2016], [
        VehicleEngineOption('M271 1.8', ['ME9.7']),
        VehicleEngineOption('M276 3.5 V6', ['MED17']),
        VehicleEngineOption('OM651 2.1', ['CDI']),
        VehicleEngineOption('OM642 3.0 V6', ['CDI']),
      ]),
    ]),
  ]),
  VehicleMakeOption('BMW', [
    VehicleModelOption('3 Series', [
      VehicleChassisOption('E90', [2005,2006,2007,2008,2009,2010,2011,2012], [
        VehicleEngineOption('N43B16 1.6', ['MSD80']),
        VehicleEngineOption('N46B20 2.0', ['MSV70']),
        VehicleEngineOption('N52B25 2.5', ['MSV70']),
        VehicleEngineOption('N52B30 3.0', ['MSV70']),
      ]),
      VehicleChassisOption('F30', [2012,2013,2014,2015,2016,2017,2018], [
        VehicleEngineOption('N20B20 2.0 Turbo', ['MEVD17']),
        VehicleEngineOption('N55B30 3.0 Turbo', ['MEVD17']),
        VehicleEngineOption('B47 2.0 Diesel', ['DDE']),
      ]),
    ]),
    VehicleModelOption('5 Series', [
      VehicleChassisOption('E60', [2003,2004,2005,2006,2007,2008,2009,2010], [
        VehicleEngineOption('M54B30 3.0', ['MS43']),
        VehicleEngineOption('N52B25 2.5', ['MSV70']),
        VehicleEngineOption('N52B30 3.0', ['MSV70']),
      ]),
    ]),
  ]),
  VehicleMakeOption('Toyota', [
    VehicleModelOption('Corolla', [
      VehicleChassisOption('E140/E150', [2007,2008,2009,2010,2011,2012,2013], [
        VehicleEngineOption('1ZR-FE 1.6', ['ECU']),
        VehicleEngineOption('2ZR-FE 1.8', ['ECU']),
      ]),
    ]),
    VehicleModelOption('Camry', [
      VehicleChassisOption('XV40', [2006,2007,2008,2009,2010,2011], [
        VehicleEngineOption('2AZ-FE 2.4', ['ECU']),
        VehicleEngineOption('2GR-FE 3.5 V6', ['ECU']),
      ]),
    ]),
    VehicleModelOption('RAV4', [
      VehicleChassisOption('XA30', [2005,2006,2007,2008,2009,2010,2011,2012], [
        VehicleEngineOption('2AZ-FE 2.4', ['ECU']),
        VehicleEngineOption('2GR-FE 3.5 V6', ['ECU']),
      ]),
    ]),
  ]),
  VehicleMakeOption('Kia', [
    VehicleModelOption('Forte', [
      VehicleChassisOption('TD', [2010,2011,2012,2013], [
        VehicleEngineOption('G4FC 1.6', ['ECU']),
        VehicleEngineOption('G4KD 2.0', ['ECU']),
      ]),
      VehicleChassisOption('YD', [2014,2015,2016,2017,2018], [
        VehicleEngineOption('G4FG 1.6', ['ECU']),
        VehicleEngineOption('G4NC 2.0', ['ECU']),
      ]),
    ]),
    VehicleModelOption('Sportage', [
      VehicleChassisOption('SL', [2011,2012,2013,2014,2015], [
        VehicleEngineOption('G4KD 2.0', ['ECU']),
        VehicleEngineOption('G4KE 2.4', ['ECU']),
      ]),
    ]),
  ]),
  VehicleMakeOption('Hyundai', [
    VehicleModelOption('Elantra', [
      VehicleChassisOption('MD', [2011,2012,2013,2014,2015,2016], [
        VehicleEngineOption('G4FG 1.6', ['ECU']),
        VehicleEngineOption('G4NA 2.0', ['ECU']),
      ]),
      VehicleChassisOption('AD', [2017,2018,2019,2020], [
        VehicleEngineOption('G4FG 1.6', ['ECU']),
        VehicleEngineOption('G4NA 2.0', ['ECU']),
      ]),
    ]),
    VehicleModelOption('Tucson', [
      VehicleChassisOption('TL', [2016,2017,2018,2019,2020], [
        VehicleEngineOption('G4NA 2.0', ['ECU']),
        VehicleEngineOption('G4FJ 1.6 Turbo', ['ECU']),
      ]),
    ]),
  ]),
  VehicleMakeOption('Honda', [
    VehicleModelOption('Civic', [
      VehicleChassisOption('FD', [2006,2007,2008,2009,2010,2011], [
        VehicleEngineOption('R18A 1.8', ['ECU']),
        VehicleEngineOption('K20Z 2.0', ['ECU']),
      ]),
    ]),
    VehicleModelOption('Accord', [
      VehicleChassisOption('CU', [2008,2009,2010,2011,2012], [
        VehicleEngineOption('K24Z 2.4', ['ECU']),
        VehicleEngineOption('J35Z 3.5 V6', ['ECU']),
      ]),
    ]),
  ]),
  VehicleMakeOption('Volkswagen', [
    VehicleModelOption('Golf', [
      VehicleChassisOption('Mk6', [2009,2010,2011,2012,2013], [
        VehicleEngineOption('1.4 TSI', ['MED17']),
        VehicleEngineOption('2.0 TDI', ['EDC17']),
      ]),
      VehicleChassisOption('Mk7', [2013,2014,2015,2016,2017,2018,2019,2020], [
        VehicleEngineOption('1.4 TSI', ['MED17']),
        VehicleEngineOption('1.5 TSI', ['MED17']),
        VehicleEngineOption('2.0 TDI', ['EDC17']),
      ]),
    ]),
    VehicleModelOption('Passat', [
      VehicleChassisOption('B7', [2011,2012,2013,2014], [
        VehicleEngineOption('1.8 TSI', ['MED17']),
        VehicleEngineOption('2.0 TDI', ['EDC17']),
      ]),
    ]),
  ]),
  VehicleMakeOption('Ford', [
    VehicleModelOption('Focus', [
      VehicleChassisOption('Mk3', [2011,2012,2013,2014,2015,2016,2017,2018], [
        VehicleEngineOption('1.6 Ti-VCT', ['ECU']),
        VehicleEngineOption('1.0 EcoBoost', ['ECU']),
        VehicleEngineOption('2.0 TDCi', ['ECU']),
      ]),
    ]),
    VehicleModelOption('Mondeo', [
      VehicleChassisOption('Mk4', [2007,2008,2009,2010,2011,2012,2013,2014], [
        VehicleEngineOption('2.0 Duratec', ['ECU']),
        VehicleEngineOption('2.0 TDCi', ['ECU']),
      ]),
    ]),
  ]),
];

VehicleMakeOption? findMake(String name) =>
    vehicleCatalog.where((x) => x.name == name).firstOrNull;
VehicleModelOption? findModel(String make, String model) =>
    findMake(make)?.models.where((x) => x.name == model).firstOrNull;
VehicleChassisOption? findChassis(String make, String model, String chassis) =>
    findModel(make, model)?.chassisOptions.where((x) => x.chassis == chassis).firstOrNull;
