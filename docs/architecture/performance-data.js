window.PERFORMANCE_DATA = {
  "nodes": [
    {
      "id": "desktop",
      "name": "Desktop UI",
      "language": "Python",
      "status": "KEEP",
      "detail": "PySide6 event loop, QPainter charts, asynchronous HTTP workers; Linux offscreen only.",
      "files": "finalbuild/apps/desktop/ui.py",
      "x": 30,
      "y": 25
    },
    {
      "id": "android",
      "name": "Android UI + transport",
      "language": "Kotlin",
      "status": "KEEP",
      "detail": "Compose, coroutines, Classic/BLE/Wi-Fi/USB native transport; backend owns decoding.",
      "files": "finalbuild/apps/mobile-android",
      "x": 300,
      "y": 25
    },
    {
      "id": "ios",
      "name": "iOS UI + transport",
      "language": "Swift",
      "status": "DEFER",
      "detail": "SwiftUI, URLSession, BLE/Wi-Fi bridge; Xcode and physical device not available.",
      "files": "finalbuild/apps/mobile-ios",
      "x": 570,
      "y": 25
    },
    {
      "id": "api",
      "name": "Backend API",
      "language": "Python",
      "status": "KEEP",
      "detail": "FastAPI/Pydantic; shared DiagnosticSession. Isolated in-process health benchmark only.",
      "files": "finalbuild/backend/api",
      "x": 840,
      "y": 25
    },
    {
      "id": "identity",
      "name": "Accounts / consent",
      "language": "Python",
      "status": "KEEP",
      "detail": "Feature-gated identity, ownership, RBAC and revocation. Native clients still use local legacy mode.",
      "files": "finalbuild/backend/ecosystem",
      "x": 30,
      "y": 190
    },
    {
      "id": "obd",
      "name": "OBD parsing",
      "language": "Python",
      "status": "KEEP",
      "detail": "ELM327, PID/DTC validation and ISO-TP. Hardware waits not measured. backend/vehicle ISO-TP stub is not the root vehicle implementation.",
      "files": "finalbuild/backend/obd; finalbuild/vehicle/isotp",
      "x": 300,
      "y": 190
    },
    {
      "id": "telemetry",
      "name": "Telemetry summary",
      "language": "Python",
      "status": "OPTIMIZE",
      "detail": "Reuse sorted filtered samples for statistics and events; exact arithmetic and event thresholds unchanged.",
      "files": "finalbuild/backend/telemetry/analysis.py; service.py",
      "x": 570,
      "y": 190
    },
    {
      "id": "rules",
      "name": "Diagnostic reasoning",
      "language": "Python",
      "status": "KEEP",
      "detail": "Deterministic rules, evidence and test-history recalculation; small measured latency.",
      "files": "finalbuild/backend/ai/reasoning",
      "x": 840,
      "y": 190
    },
    {
      "id": "llm",
      "name": "Local / remote LLM",
      "language": "Python",
      "status": "DEFER",
      "detail": "HTTP orchestration to llama-server/native inference; model unavailable, no inference measurement.",
      "files": "finalbuild/backend/ai/llm",
      "x": 30,
      "y": 355
    },
    {
      "id": "rag",
      "name": "RAG / catalog",
      "language": "Python",
      "status": "DEFER",
      "detail": "Lexical/vector adapters and catalog data. Scan/index candidates need representative production workload.",
      "files": "finalbuild/backend/ai/rag; global_data.py",
      "x": 300,
      "y": 355
    },
    {
      "id": "db",
      "name": "Persistence",
      "language": "SQL",
      "status": "DEFER",
      "detail": "SQLAlchemy JSON snapshots + optional PostgreSQL; synthetic SQLite index benchmark is not production capacity.",
      "files": "finalbuild/backend/diagnostic/session_persistence.py",
      "x": 570,
      "y": 355
    },
    {
      "id": "native",
      "name": "Native mean prototype",
      "language": "C++",
      "status": "C++ CANDIDATE",
      "detail": "C++20 C ABI, ctypes and copy cost measured; not integrated. Simpler fmean wins experiment; exact rounding not universally established.",
      "files": "finalbuild/experiments/native_mean",
      "x": 840,
      "y": 355
    },
    {
      "id": "future",
      "name": "Future services",
      "language": "Python",
      "status": "DEFER",
      "detail": "Durable scheduler, notifications, merchant/admin business operations and sync remain incomplete; not benchmarked as implemented.",
      "files": "docs/FEATURE_MATRIX.md",
      "x": 30,
      "y": 520
    }
  ],
  "edges": [
    [
      "desktop",
      "api"
    ],
    [
      "android",
      "api"
    ],
    [
      "ios",
      "api"
    ],
    [
      "api",
      "identity"
    ],
    [
      "api",
      "obd"
    ],
    [
      "api",
      "telemetry"
    ],
    [
      "api",
      "rules"
    ],
    [
      "rules",
      "llm"
    ],
    [
      "rules",
      "rag"
    ],
    [
      "api",
      "db"
    ]
  ],
  "baseline": {
    "schema_version": 1,
    "python": "3.13.5 (main, Aug 10 2026, 12:06:59) [GCC 14.2.0]",
    "platform": "Linux-6.18.55-x86_64-with-glibc2.41",
    "git_head": "540e00f07b8f60c2788c8d12dea1200817669afb",
    "clock": "perf_counter_ns",
    "seed": 429,
    "results": {
      "diagnostic_analysis": {
        "iterations": 30,
        "warmups": 5,
        "p50_ms": 0.595091,
        "p95_ms": 0.960246,
        "p99_ms": 0.991914,
        "operations_per_second": 1506.4580340953669,
        "cpu_seconds": 0.019920742999999907,
        "wall_seconds": 0.01991426201129798,
        "cpu_percent_one_core": 100.03254445832967,
        "traced_peak_bytes": 52217,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          573,
          0,
          0
        ]
      },
      "pid_snapshot": {
        "iterations": 30,
        "warmups": 5,
        "p50_ms": 0.0242015,
        "p95_ms": 0.057987,
        "p99_ms": 0.139891,
        "operations_per_second": 32962.64996141297,
        "cpu_seconds": 0.0009148599999999618,
        "wall_seconds": 0.0009101210016524419,
        "cpu_percent_one_core": 100.52069981232337,
        "traced_peak_bytes": 2303,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          14,
          0,
          0
        ]
      },
      "dtc_decode": {
        "iterations": 30,
        "warmups": 5,
        "p50_ms": 0.001677,
        "p95_ms": 0.003816,
        "p99_ms": 0.028763,
        "operations_per_second": 317551.0524781139,
        "cpu_seconds": 9.837599999995561e-05,
        "wall_seconds": 9.447299817111343e-05,
        "cpu_percent_one_core": 104.13134112857612,
        "traced_peak_bytes": 464,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          4,
          0,
          0
        ]
      },
      "session_json": {
        "iterations": 30,
        "warmups": 5,
        "p50_ms": 0.004707,
        "p95_ms": 0.007782,
        "p99_ms": 0.092089,
        "operations_per_second": 120237.58781125915,
        "cpu_seconds": 0.0002535570000001819,
        "wall_seconds": 0.00024950600345619023,
        "cpu_percent_one_core": 101.62360684227102,
        "traced_peak_bytes": 1426,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          4,
          0,
          0
        ]
      },
      "telemetry_summary_1000": {
        "iterations": 30,
        "warmups": 5,
        "p50_ms": 1.8905370000000001,
        "p95_ms": 3.203024,
        "p99_ms": 3.859453,
        "operations_per_second": 462.8894506505687,
        "cpu_seconds": 0.06481730399999996,
        "wall_seconds": 0.06481029100541491,
        "cpu_percent_one_core": 100.0108208040363,
        "traced_peak_bytes": 35956,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          1094,
          0,
          0
        ]
      },
      "telemetry_summary_10000": {
        "iterations": 30,
        "warmups": 5,
        "p50_ms": 21.6640345,
        "p95_ms": 31.762082,
        "p99_ms": 33.210543,
        "operations_per_second": 43.90976248733629,
        "cpu_seconds": 0.6809249100000003,
        "wall_seconds": 0.6832193640002515,
        "cpu_percent_one_core": 99.66417023270284,
        "traced_peak_bytes": 688168,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          1,
          4,
          9
        ]
      },
      "telemetry_summary_50000": {
        "iterations": 30,
        "warmups": 5,
        "p50_ms": 189.2053195,
        "p95_ms": 223.155404,
        "p99_ms": 233.758288,
        "operations_per_second": 5.251978826524044,
        "cpu_seconds": 5.711892613000001,
        "wall_seconds": 5.712132701009978,
        "cpu_percent_one_core": 99.99579687618368,
        "traced_peak_bytes": 3888072,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          0,
          10,
          162
        ]
      },
      "http_health_inprocess": {
        "iterations": 30,
        "warmups": 5,
        "p50_ms": 2.34382,
        "p95_ms": 2.745305,
        "p99_ms": 3.452039,
        "operations_per_second": 418.0649021476908,
        "cpu_seconds": 0.0739952929999994,
        "wall_seconds": 0.0717591930006165,
        "cpu_percent_one_core": 103.11611642478155,
        "traced_peak_bytes": 71287,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          1317,
          1,
          0
        ]
      },
      "sqlite_indexed_history_100": {
        "iterations": 30,
        "warmups": 5,
        "p50_ms": 0.029369,
        "p95_ms": 0.089024,
        "p99_ms": 0.348465,
        "operations_per_second": 23400.570858412484,
        "cpu_seconds": 0.001286733000000595,
        "wall_seconds": 0.0012820200063288212,
        "cpu_percent_one_core": 100.36762247457197,
        "traced_peak_bytes": 4499,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          138,
          0,
          0
        ]
      }
    },
    "backend_import_fresh_process_ms": [
      746.929736007587,
      713.5045369941508,
      793.1246000080137,
      706.8880839942722,
      695.1823029958177
    ],
    "profile": "baseline.prof",
    "limitations": [
      "Synthetic shuffled telemetry; four channels at 10 Hz each; not hardware throughput.",
      "Fresh process imports use warm OS file cache; true cold boot NOT MEASURED.",
      "HTTP is in-process TestClient, not socket/load capacity.",
      "SQLite is an isolated in-memory indexed fixture, not deployed PostgreSQL.",
      "Adapter/ECU/network latency, real LLM/RAG model inference, Windows/iOS, GPU/frame times and RSS NOT MEASURED."
    ]
  },
  "paired": {
    "baseline_ref": "540e00f",
    "reference_sha256": "a8db6b07ca708ce388ac8d3031e7e8734c57d233bb64a4b6b9aea31d213a97f2",
    "iterations": 40,
    "ordering": "alternating AB/BA",
    "results": {
      "1000": {
        "baseline": {
          "p50_ms": 1.7613185,
          "p95_ms": 2.247405,
          "p99_ms": 2.987069,
          "raw_ms": [
            1.927313,
            2.841339,
            2.206633,
            1.871299,
            2.247405,
            1.769395,
            1.782164,
            1.767533,
            1.680921,
            1.649364,
            1.747142,
            1.642113,
            1.669785,
            1.744228,
            1.671878,
            2.086613,
            2.087183,
            1.843516,
            1.888995,
            1.649805,
            1.654802,
            1.641953,
            2.0454,
            1.703005,
            1.781873,
            2.987069,
            1.775965,
            1.81941,
            1.755104,
            1.7722,
            1.929065,
            1.67988,
            1.860653,
            1.676114,
            1.658578,
            1.635503,
            1.67347,
            1.683215,
            1.630285,
            1.658858
          ]
        },
        "optimized": {
          "p50_ms": 1.559048,
          "p95_ms": 2.122897,
          "p99_ms": 5.392277,
          "raw_ms": [
            1.468121,
            5.392277,
            1.829436,
            2.086333,
            1.608032,
            1.55386,
            1.459338,
            1.4741,
            1.617466,
            1.469874,
            1.564236,
            1.58044,
            1.485538,
            1.46743,
            2.122897,
            1.617336,
            3.082894,
            1.733962,
            1.608833,
            1.46001,
            1.457726,
            1.464276,
            1.738559,
            1.511737,
            1.55369,
            1.477335,
            1.723436,
            1.578007,
            1.912491,
            1.542554,
            1.639158,
            1.481392,
            1.700771,
            1.459358,
            1.547981,
            1.536705,
            1.466689,
            1.568082,
            1.473179,
            1.574312
          ]
        },
        "p50_improvement_percent": 11.4840388038847,
        "equivalence": "PASS",
        "resources": {
          "baseline": {
            "iterations": 10,
            "warmups": 5,
            "p50_ms": 1.7686735,
            "p95_ms": 2.711053,
            "p99_ms": 2.711053,
            "operations_per_second": 513.2715337750537,
            "cpu_seconds": 0.019488681000000008,
            "wall_seconds": 0.019482864998281002,
            "cpu_percent_one_core": 100.02985188122753,
            "traced_peak_bytes": 35956,
            "allocation_count": "NOT MEASURED",
            "gc_counts_after": [
              1066,
              0,
              0
            ]
          },
          "optimized": {
            "iterations": 10,
            "warmups": 5,
            "p50_ms": 1.54684,
            "p95_ms": 1.966662,
            "p99_ms": 1.966662,
            "operations_per_second": 618.1096995052286,
            "cpu_seconds": 0.016184207999999978,
            "wall_seconds": 0.016178357996977866,
            "cpu_percent_one_core": 100.03615943610103,
            "traced_peak_bytes": 35956,
            "allocation_count": "NOT MEASURED",
            "gc_counts_after": [
              1066,
              0,
              0
            ]
          }
        }
      },
      "10000": {
        "baseline": {
          "p50_ms": 20.676793,
          "p95_ms": 23.957675,
          "p99_ms": 44.322878,
          "raw_ms": [
            21.232419,
            21.377267,
            20.65519,
            19.328942,
            22.309442,
            21.751992,
            19.606681,
            20.192514,
            20.502019,
            20.698396,
            44.322878,
            21.44527,
            20.149919,
            21.325249,
            20.189069,
            19.44669,
            19.605009,
            20.864655,
            21.250076,
            20.419475,
            20.081747,
            23.957675,
            21.476196,
            20.959779,
            20.727198,
            20.790094,
            19.100528,
            19.814895,
            19.676376,
            21.369636,
            19.609084,
            22.618637,
            24.432149,
            20.844185,
            20.116318,
            19.322303,
            19.883858,
            20.194476,
            20.328518,
            20.750274
          ]
        },
        "optimized": {
          "p50_ms": 17.8752685,
          "p95_ms": 20.377592,
          "p99_ms": 22.165515,
          "raw_ms": [
            15.9081,
            16.827275,
            17.562842,
            17.290853,
            18.040562,
            18.654097,
            19.058716,
            18.393724,
            18.095946,
            16.986224,
            17.206887,
            17.37483,
            18.03275,
            21.314443,
            16.914907,
            17.674921,
            17.407789,
            17.958449,
            18.008815,
            19.002711,
            17.450974,
            19.007048,
            19.770828,
            18.719935,
            17.022448,
            17.282591,
            16.699442,
            16.610869,
            17.473288,
            17.904197,
            16.728026,
            18.190188,
            20.377592,
            17.991097,
            17.458625,
            16.460302,
            18.43102,
            18.63678,
            22.165515,
            17.84634
          ]
        },
        "p50_improvement_percent": 13.549124857031746,
        "equivalence": "PASS",
        "resources": {
          "baseline": {
            "iterations": 10,
            "warmups": 5,
            "p50_ms": 22.5090925,
            "p95_ms": 23.16431,
            "p99_ms": 23.16431,
            "operations_per_second": 44.62299154632443,
            "cpu_seconds": 0.2241028380000003,
            "wall_seconds": 0.22409972199238837,
            "cpu_percent_one_core": 100.00139045581325,
            "traced_peak_bytes": 688168,
            "allocation_count": "NOT MEASURED",
            "gc_counts_after": [
              4,
              8,
              3
            ]
          },
          "optimized": {
            "iterations": 10,
            "warmups": 5,
            "p50_ms": 20.0095455,
            "p95_ms": 24.164726,
            "p99_ms": 24.164726,
            "operations_per_second": 48.81344783608974,
            "cpu_seconds": 0.2048569819999999,
            "wall_seconds": 0.20486157899722457,
            "cpu_percent_one_core": 99.99775604715771,
            "traced_peak_bytes": 688168,
            "allocation_count": "NOT MEASURED",
            "gc_counts_after": [
              4,
              8,
              3
            ]
          }
        }
      },
      "50000": {
        "baseline": {
          "p50_ms": 186.619181,
          "p95_ms": 240.183667,
          "p99_ms": 245.491281,
          "raw_ms": [
            173.868833,
            178.402481,
            204.20284,
            175.549073,
            172.51249,
            211.450237,
            180.443285,
            187.422167,
            245.491281,
            235.255341,
            176.758375,
            178.946531,
            177.827205,
            191.516183,
            209.135821,
            194.757153,
            179.249816,
            185.816195,
            178.715492,
            164.764319,
            173.90747,
            169.117926,
            179.443187,
            176.891855,
            174.51146,
            183.600039,
            187.796349,
            188.675924,
            218.020891,
            240.183667,
            240.963646,
            194.482404,
            232.142891,
            215.796241,
            181.719716,
            182.550938,
            215.203047,
            229.867288,
            188.495982,
            205.337573
          ]
        },
        "optimized": {
          "p50_ms": 148.372326,
          "p95_ms": 190.235553,
          "p99_ms": 234.003956,
          "raw_ms": [
            124.92126,
            148.12617,
            171.830022,
            138.78392,
            152.887573,
            234.003956,
            141.970459,
            142.17735,
            169.555692,
            155.990796,
            137.101476,
            162.993102,
            145.155405,
            148.618482,
            147.31547,
            153.678093,
            139.536523,
            139.925668,
            153.181604,
            153.038007,
            128.443745,
            131.493318,
            135.58444,
            142.215618,
            141.506349,
            152.060896,
            149.439768,
            146.048129,
            160.76116,
            170.14617,
            158.042891,
            173.557152,
            132.582789,
            140.213231,
            142.035436,
            147.278713,
            190.235553,
            215.743005,
            167.228005,
            151.706017
          ]
        },
        "p50_improvement_percent": 20.49460017724545,
        "equivalence": "PASS",
        "resources": {
          "baseline": {
            "iterations": 10,
            "warmups": 5,
            "p50_ms": 172.81210049999999,
            "p95_ms": 234.965305,
            "p99_ms": 234.965305,
            "operations_per_second": 5.625279017017722,
            "cpu_seconds": 1.777544204999998,
            "wall_seconds": 1.7776895989954937,
            "cpu_percent_one_core": 99.99182118207938,
            "traced_peak_bytes": 3888072,
            "allocation_count": "NOT MEASURED",
            "gc_counts_after": [
              0,
              10,
              57
            ]
          },
          "optimized": {
            "iterations": 10,
            "warmups": 5,
            "p50_ms": 163.3105875,
            "p95_ms": 180.858384,
            "p99_ms": 180.858384,
            "operations_per_second": 6.338166402187757,
            "cpu_seconds": 1.5777035869999985,
            "wall_seconds": 1.5777433670009486,
            "cpu_percent_one_core": 99.997478677345,
            "traced_peak_bytes": 3888072,
            "allocation_count": "NOT MEASURED",
            "gc_counts_after": [
              4,
              3,
              21
            ]
          }
        }
      }
    }
  },
  "native": {
    "results": {
      "python_exact_mean": {
        "pipeline": {
          "iterations": 40,
          "warmups": 5,
          "p50_ms": 18.05646,
          "p95_ms": 19.681492,
          "p99_ms": 20.910664,
          "operations_per_second": 54.955837084268644,
          "cpu_seconds": 0.727336524,
          "wall_seconds": 0.7278571689967066,
          "cpu_percent_one_core": 99.92846879595565,
          "traced_peak_bytes": 688168,
          "allocation_count": "NOT MEASURED",
          "gc_counts_after": [
            1,
            10,
            11
          ]
        },
        "max_absolute_numeric_difference": 0.0,
        "tolerance_check": "PASS (fixture only; not exact equivalence)"
      },
      "python_fmean_experiment": {
        "pipeline": {
          "iterations": 40,
          "warmups": 5,
          "p50_ms": 10.999602,
          "p95_ms": 20.537872,
          "p99_ms": 28.166502,
          "operations_per_second": 78.07341253486918,
          "cpu_seconds": 0.5111900539999998,
          "wall_seconds": 0.5123383070022101,
          "cpu_percent_one_core": 99.7758799241601,
          "traced_peak_bytes": 688168,
          "allocation_count": "NOT MEASURED",
          "gc_counts_after": [
            1,
            10,
            11
          ]
        },
        "max_absolute_numeric_difference": 1.1368683772161603e-13,
        "tolerance_check": "PASS (fixture only; not exact equivalence)"
      },
      "cpp_copy_included_experiment": {
        "pipeline": {
          "iterations": 40,
          "warmups": 5,
          "p50_ms": 13.307042,
          "p95_ms": 17.553157,
          "p99_ms": 18.832294,
          "operations_per_second": 72.89430379545963,
          "cpu_seconds": 0.548698913,
          "wall_seconds": 0.5487397219985723,
          "cpu_percent_one_core": 99.99256314115118,
          "traced_peak_bytes": 688168,
          "allocation_count": "NOT MEASURED",
          "gc_counts_after": [
            13,
            8,
            13
          ]
        },
        "max_absolute_numeric_difference": 0.0,
        "tolerance_check": "PASS (fixture only; not exact equivalence)"
      },
      "native_prepacked_micro_only": {
        "iterations": 1000,
        "warmups": 5,
        "p50_ms": 0.00681,
        "p95_ms": 0.00692,
        "p99_ms": 0.020911,
        "operations_per_second": 136566.16403404035,
        "cpu_seconds": 0.007327663000000317,
        "wall_seconds": 0.007322457997361198,
        "cpu_percent_one_core": 100.07108272442116,
        "traced_peak_bytes": 340,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          6,
          0,
          0
        ]
      },
      "native_mean_with_copy_micro": {
        "iterations": 1000,
        "warmups": 5,
        "p50_ms": 0.188409,
        "p95_ms": 0.306391,
        "p99_ms": 0.41823,
        "operations_per_second": 4754.588581882447,
        "cpu_seconds": 0.21032713899999989,
        "wall_seconds": 0.21032314001058694,
        "cpu_percent_one_core": 100.00190135494019,
        "traced_peak_bytes": 40196,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          6,
          0,
          0
        ]
      },
      "python_fmean_micro": {
        "iterations": 1000,
        "warmups": 5,
        "p50_ms": 0.023245,
        "p95_ms": 0.025668,
        "p99_ms": 0.067131,
        "operations_per_second": 39201.8672352073,
        "cpu_seconds": 0.025506887000000145,
        "wall_seconds": 0.025508988997898996,
        "cpu_percent_one_core": 99.99175977574406,
        "traced_peak_bytes": 116,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          4,
          0,
          0
        ]
      },
      "python_exact_mean_micro": {
        "iterations": 1000,
        "warmups": 5,
        "p50_ms": 0.729919,
        "p95_ms": 1.183382,
        "p99_ms": 1.249893,
        "operations_per_second": 1254.1816768818392,
        "cpu_seconds": 0.7972829309999998,
        "wall_seconds": 0.7973326499923132,
        "cpu_percent_one_core": 99.99376433508473,
        "traced_peak_bytes": 2948,
        "allocation_count": "NOT MEASURED",
        "gc_counts_after": [
          9,
          0,
          0
        ]
      }
    },
    "decision": "NOT INTEGRATED: finite-only contract, floating-point equivalence not universal; compare simpler fmean first. GIL release only during ctypes call, packing holds GIL. No JNI/iOS/Windows validation."
  }
};
