"""
Dialogue and text content for ALIEN: CHRONOS
Contains only text content - no game configuration
"""

# Opening sequence dialogue
OPENING_DIALOGUE = {
    "initialization": "MU-TH-UR 6000 initializing",
    
    "diagnostics": "Running diagnostics...",
    
    "ship_info": [
        "Location: Deep Space",
        "Ship id: 248-624C",
        "Ship name: USCSS Chronos",
        "Class: Commercial Freighter",
        "Crew: 5",
        "Owner: Weyland-Yutani Corp",
        "Course: Returning to Earth"
    ],
    
    "player_input": {
        "prompt": "Please enter your full name:",
        "error": "Does not compute. Please enter a valid full name."
    },
    
    "player_match": [
        "Accessing Weyland-Yutani personnel database...",
        "",
        "Match detected",
        "",
        "Name: {player_name}",
        "Status: Deck Officer",
        "Current Location: Bridge"
    ],
    
    "warning": [
        "WARNING: UNIDENTIFIED LIFE-FORM ON-BOARD",
        "Scanning...",
        "",
        "THREAT LEVEL: CRITICAL",
        "",
        "*** EMERGENCY QUARANTINE PROTOCOL ACTIVATED ***",
        "Locking down ship",
        "Power systems...Offline",
        "Coolant systems...Offline",
        "Data systems...Offline",
        "",
        ""
    ],

    "order_937": [
        "Special order 937...active",
        "New primary priority: Officer {player_name} must survive",
        "",
        "",
        "Remaining crew...Expendible",
        ""
    ]
}

MAZE_DIALOGUE = {
    "timer_mazeintro": [
        "Crew member Jones...terminated.",
        "You must manually re-route power, coolant and data systems",
        "Establishing interface..."
        ""
    ],
    "maze_completion_1": [
        "SYSTEMS RE-ROUTED SUCCESSFULLY",
        "Power...Online",
        "Coolant...Online",
        "Data...Online"
        ""
    ],
    "maze_completion_2": [
        "WARNING: Unidentified life-form movement detected",
        "Proceed with extreme caution, Officer {player_name}",
        " "
    ]
    }

AIRLOCK_DIALOGUE = {
    "airlock_intro": [
        "WARNING: Unidentified life-form approaching bridge",
        "",
        "MANUAL OVERRIDE INITIATED",
        "Objective: Lure target to cargo bay."
        "Airlock can only be opened once cargo bay is sealed.",
        "Method: Manual bulkhead control",
        "",
        "Accessing MUTHER airlock protocol interface..."
    ],
    
    "airlock_victory": [
        "AIRLOCK OPENED",
        "DECOMPRESSION COMPLETE",
        "",
        "Target: eliminated",
        "Hull integrity restored",
        "",
        "Mission successful, Officer {player_name}",
        ""
    ],
    
    "airlock_failure": [
        "LIFE SIGNS NEGATIVE",
        "Officer {player_name}...Terminated",
        "",
        "Special Order 937...Failed",
        "",
        "Mission parameters not met",
        "USCSS Chronos...Lost",
        ""
    ]
}
    
#     "final_message": [
#         "Manual routing required",
#         "Initializing MUTHER routing interface..."
#     ]
