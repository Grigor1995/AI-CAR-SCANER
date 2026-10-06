from __future__ import annotations
import re
from .models import DiagnosticSession, EvidenceSource, EvidenceStatus, Hypothesis, DiagnosticTest, SessionState


class DiagnosticReasoningEngine:
    """Context-aware deterministic diagnostic reasoning.

    This layer intentionally does not declare a failed component as confirmed. It
    classifies the current evidence into diagnostic categories and creates a
    scenario-specific hypothesis set. LLMs can later explain/orchestrate the
    result, but they do not replace these deterministic facts.
    """

    def analyze(self, session: DiagnosticSession) -> DiagnosticSession:
        facts = [e.fact.lower() for e in session.evidence]
        text = " ".join(facts)
        dtcs = {d.code.upper() for d in session.dtcs}

        categories: list[tuple[str, str]] = []
        self._add_dtc_categories(dtcs, categories)
        self._add_symptom_categories(text, categories)
        self._add_context_categories(text, categories)

        # Preserve order while removing duplicates.
        seen: set[str] = set()
        unique: list[tuple[str, str]] = []
        for category, statement in categories:
            if category not in seen:
                seen.add(category)
                unique.append((category, statement))

        session.hypotheses = [
            Hypothesis(category=category, statement=statement) for category, statement in unique
        ]
        return self._recommend(session, text, dtcs)

    @staticmethod
    def _add_dtc_categories(dtcs: set[str], categories: list[tuple[str, str]]) -> None:
        for code in sorted(dtcs):
            if re.fullmatch(r"P03\d{2}", code):
                categories.append(("ignition / combustion", f"The {code} family indicates a misfire/combustion issue; identify whether it follows fuel mode, load, or cylinder."))
                categories.append(("intake", f"Misfire can also be influenced by intake/airflow conditions; verify air-fuel and mechanical evidence before concluding component failure."))
            elif code in {"P0171", "P0174"}:
                categories.append(("lean mixture", f"{code} indicates a lean condition; separate air leak, fuel delivery, and sensor/model causes."))
            elif code in {"P0172", "P0175"}:
                categories.append(("rich mixture", f"{code} indicates a rich condition; separate excess fuel from incorrect airflow/lambda feedback."))
            elif code in {"P0100", "P0101", "P0102", "P0103", "P0104"}:
                categories.append(("air metering / MAF", f"{code} points to the air-metering signal/system; verify signal plausibility, wiring, and unmetered air."))
            elif code in {"P0115", "P0116", "P0117", "P0118", "P0119"}:
                categories.append(("coolant temperature sensing", f"{code} points to coolant-temperature sensing/rationality; compare cold-start and warmed-up readings."))
            elif re.fullmatch(r"P01[3-6]\d", code):
                categories.append(("oxygen sensor / fuel feedback", f"{code} points to oxygen-sensor/fuel-feedback behavior; compare commanded/observed mixture and sensor response."))
            elif code in {"P0420", "P0430"}:
                categories.append(("catalyst efficiency", f"{code} indicates catalyst-efficiency monitoring; verify sensor behavior and exhaust conditions before attributing catalyst failure."))
            elif code in {"P0016", "P0017", "P0018", "P0019"}:
                categories.append(("cam/crank correlation", f"{code} indicates a cam/crank correlation concern; verify timing correlation before considering mechanical timing faults."))
            elif re.fullmatch(r"P07[23]\d", code) or code in {"P0730", "P0731", "P0732", "P0733", "P0734", "P0735"}:
                categories.append(("transmission control / gear ratio", f"{code} indicates a transmission control or ratio concern; compare commanded versus actual gear, speed, and slip."))
            elif code in {"P0560", "P0561", "P0562", "P0563"}:
                categories.append(("power supply / voltage", f"{code} points to system-voltage behavior; verify battery, charging voltage, and voltage stability under load."))
            elif code.startswith("U"):
                categories.append(("vehicle network communication", f"{code} is a network/communication DTC; verify bus health, ECU reachability, power/ground, and gateway routing."))

    @staticmethod
    def _add_symptom_categories(text: str, categories: list[tuple[str, str]]) -> None:
        if any(x in text for x in ("no start", "won't start", "does not start", "cranks but")):
            categories.append(("starting system / engine start", "The reported no-start behavior requires separating crank, authorization, fuel, ignition, and engine-speed evidence."))
        if any(x in text for x in ("stall", "stalls", "dies while driving")):
            categories.append(("engine stalling", "The stalling condition should be correlated with RPM, fuel pressure, ignition, and relevant ECU status."))
        if any(x in text for x in ("overheat", "overheating", "temperature high", "coolant boiling")):
            categories.append(("cooling system", "The overheating symptom requires measured coolant temperature, fan behavior, coolant circulation, and system-level checks."))
        if any(x in text for x in ("battery", "slow crank", "weak crank", "electrical")):
            categories.append(("electrical power supply", "The electrical symptom should be validated with battery and charging voltage measurements under defined conditions."))

    @staticmethod
    def _add_context_categories(text: str, categories: list[tuple[str, str]]) -> None:
        lpg_only = "lpg" in text and ("petrol normal" in text or "normal on petrol" in text or "only on lpg" in text)
        if lpg_only and any(x in text for x in ("misfire", "shak", "jerk")):
            categories.extend([
                ("LPG injection", "The fault appears fuel-mode specific; verify LPG pressure and injector delivery before condemning ignition hardware."),
                ("LPG fuel delivery", "The fault appears fuel-mode specific; verify LPG pressure and injector delivery before condemning ignition hardware."),
                ("LPG calibration", "Fuel-mode-specific behavior can result from mixture/calibration errors; compare trims and commanded/actual gas conditions."),
                ("ignition under LPG load", "A marginal ignition system can misfire under the higher demand associated with LPG/load; confirm with cylinder-specific evidence."),
            ])

        if "acceleration" in text or "under load" in text:
            categories.append(("load-dependent behavior", "The event is operating-condition dependent; reproduce it with synchronized RPM/load measurements."))
        if "idle" in text and any(x in text for x in ("rough", "shaking", "unstable")):
            categories.append(("idle stability / air-fuel control", "The idle symptom should be separated into airflow, mixture, ignition, and mechanical contributors."))
        if "smoke" in text or "oil consumption" in text:
            categories.append(("oil / combustion condition", "Visible smoke or oil-consumption evidence requires separating combustion, ventilation, and lubricant-related causes."))

    @staticmethod
    def _recommend(session: DiagnosticSession, text: str, dtcs: set[str]) -> DiagnosticSession:
        # Recommendations are scenario-specific. These are diagnostic actions,
        # not component verdicts.
        recommendations: list[DiagnosticTest] = []

        def add(name: str, purpose: str, target: list[str], safety: list[str] | None = None, risk: str = "LOW") -> None:
            recommendations.append(DiagnosticTest(
                name=name,
                purpose=purpose,
                safety_notes=safety or [],
                target_hypotheses=target,
                prerequisites=[],
                priority_score=0.0,
                risk_level=risk,
            ))

        cats = {h.category for h in session.hypotheses}
        if cats & {"LPG injection", "LPG fuel delivery", "LPG calibration"}:
            add("Measure LPG pressure at idle and under load", "Determine whether gas pressure remains stable during the symptom window.", ["LPG fuel delivery", "LPG calibration"], ["Use approved LPG diagnostic procedures and keep ignition sources controlled."])
            add("Compare STFT/LTFT on petrol versus LPG", "Separate a fuel-system-specific mixture problem from an engine-wide control problem.", ["LPG calibration", "LPG fuel delivery", "lean mixture", "rich mixture"])
            add("Compare LPG injector contribution / balance", "Check whether one cylinder receives materially different LPG delivery.", ["LPG fuel delivery"], ["Follow LPG system manufacturer procedures."], "MEDIUM")
        if "ignition / combustion" in cats or "ignition under LPG load" in cats:
            add("Compare cylinder misfire counters under the same load", "Determine whether the event remains isolated to a cylinder and under which fuel mode it occurs.", ["ignition / combustion", "ignition under LPG load"])
            add("Check ignition performance under controlled load", "Correlate ignition behavior with the exact RPM/load/fuel condition where the misfire occurs.", ["ignition / combustion", "ignition under LPG load"], ["Use properly rated test equipment and workshop precautions."], "MEDIUM")
        if "air metering / MAF" in cats:
            add("Validate MAF signal against RPM/load plausibility", "Determine whether the airflow signal is plausible across operating points.", ["air metering / MAF"])
            add("Inspect intake and MAF wiring/connectors", "Separate wiring/connector faults from a sensor-signal problem.", ["air metering / MAF", "lean mixture"])
        if "lean mixture" in cats:
            add("Check for unmetered-air leak", "Look for air entering downstream of the expected metering point.", ["lean mixture"])
            add("Measure fuel pressure under load", "Verify that fuel delivery can maintain required pressure during the reported condition.", ["lean mixture"])
        if "rich mixture" in cats:
            add("Check injector leakage / fuel pressure", "Separate excess fuel delivery from feedback or airflow-model errors.", ["rich mixture"])
            add("Compare lambda response and fuel trims", "Determine whether the rich condition is persistent and how the feedback system responds.", ["rich mixture", "oxygen sensor / fuel feedback"])
        if "oxygen sensor / fuel feedback" in cats:
            add("Check O2 sensor response and heater behavior", "Validate sensor response speed, plausibility, and heater-related behavior.", ["oxygen sensor / fuel feedback"])
        if "catalyst efficiency" in cats:
            add("Compare upstream/downstream O2 behavior after warm-up", "Verify catalyst-monitoring conditions before attributing low efficiency to the catalyst itself.", ["catalyst efficiency"])
        if "coolant temperature sensing" in cats or "cooling system" in cats:
            add("Compare ECU coolant temperature with independent measurement", "Separate sensor/rationality problems from actual thermal conditions.", ["coolant temperature sensing", "cooling system"])
            add("Verify cooling fan command and actual fan operation", "Determine whether fan activation matches the measured temperature condition.", ["cooling system"])
        if "cam/crank correlation" in cats:
            add("Compare cam/crank correlation data and timing values", "Validate correlation before considering mechanical timing intervention.", ["cam/crank correlation"], ["Follow manufacturer timing and engine-running safety procedures."], "MEDIUM")
        if "transmission control / gear ratio" in cats:
            add("Compare commanded gear, actual gear and slip", "Determine whether the ratio deviation is hydraulic, sensor-related, or control-related.", ["transmission control / gear ratio"])
            add("Check transmission fluid temperature and pressure evidence", "Correlate the event with operating temperature and available hydraulic evidence.", ["transmission control / gear ratio"], ["Follow transmission service safety procedures."], "MEDIUM")
        if "power supply / voltage" in cats or "electrical power supply" in cats:
            add("Measure battery voltage at rest and during crank", "Determine whether battery voltage is adequate and stable during starting load.", ["power supply / voltage", "electrical power supply"])
            add("Measure charging voltage under electrical load", "Check alternator/regulator behavior across representative loads.", ["power supply / voltage", "electrical power supply"])
        if "vehicle network communication" in cats:
            add("Capture CAN traffic and verify ECU/gateway responses", "Separate bus integrity, gateway routing, ECU availability, and application-level faults.", ["vehicle network communication"])
        if "starting system / engine start" in cats:
            add("Verify engine speed, battery voltage and start authorization", "Separate crank/electrical/authorization issues before fuel or ignition parts are isolated.", ["starting system / engine start", "power supply / voltage"])
        if "engine stalling" in cats:
            add("Correlate stall event with RPM, fuel pressure and ECU status", "Determine whether the stall is caused by fuel, ignition, speed-signal, or control evidence.", ["engine stalling", "ignition / combustion"])
        if "idle stability / air-fuel control" in cats:
            add("Compare idle fuel trims, MAF/MAP and misfire counters", "Separate air-fuel control from ignition and mechanical idle contributors.", ["idle stability / air-fuel control", "lean mixture", "air metering / MAF"])

        # Safe generic fallback for unknown scenarios.
        if not recommendations:
            add("Collect baseline live data and reproduce the symptom", "Establish time-synchronized RPM, load, temperature, and relevant sensor evidence before narrowing the fault domain.", [])
            add("Read ECU DTCs and freeze-frame data", "Obtain ECU-reported evidence and operating conditions associated with the event.", [])

        session.recommendations = recommendations
        session.state = SessionState.TESTING
        return session
