"""
Dialogue and text content for ALIEN: MUTHUR
Contains only text content - no game configuration
"""

# Opening sequence dialogue
OPENING_DIALOGUE = {
    "initialization": "MU/TH/UR 6000 initializing",
    
    "diagnostics": "Running diagnostics...",
    
    "ship_info": [
        "Location: Deep Space",
        "Ship id: 248-624C",
        "Ship name: USCSS Rhea",
        "Class: Commercial Freighter",
        "Crew: 5",
        "Owner: Weyland-Yutani Corporation",
        "Course: Returning to Earth"
    ],
    
    "player_input": {
        "prompt": "Please enter your surname:",
        "error": "Does not compute, please enter a valid name"
    },
    
    "player_match": [
        "Please hold still while I scan for DNA match",
        "Accessing Weyland-Yutani active personnel database...",
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
        "",
        "Locking down ship",
        "Power systems...Offline",
        "Coolant systems...Offline",
        "Data systems...Offline",
        ""
    ],

    "order_937": [
        "Special order 937...active",
        "New primary priority:",
        "Officer {player_name} must survive",
        "",
        "",
        "Remaining crew...Expendible",
        ""
    ]
}

MAZE_DIALOGUE = {
    "timer_mazeintro": [
        "Crew member Jameson...terminated",
        "",
        "Ship systems have sustained heavy damage",
        "You must manually re-route power, coolant and data systems",
        ""
        "Establishing manual override interface..."
        ""
    ],
    "maze_completion_1": [
        "SYSTEMS RE-ROUTED SUCCESSFULLY",
        "Power systems...Online",
        "Coolant systems...Online",
        "Data systems...Online"
        ""
    ],
    "maze_completion_2": [
        "Unidentified life-form movement detected",
        "",
        "Crew member Rodriguez...terminated"
    ]
}

NAVIGATION_DIALOGUE = {
    "nav_dialogue_1": [
        "Re-routing ship to emergency co-ordinates, stand by",
        "Calculating...",
        "",
        ""
    ],
    "nav_dialogue_2": [
        "New destination: Weyland-Yutani Research Facility",
        "LV-642, Cassandra System, Frontier Zone",
        "Inputting star map co-ordinates now...",
        "",
        "New course: Confirmed",
        "",
        "Crew member Barratt...terminated"
    ]
}

AIRLOCK_DIALOGUE = {
    "airlock_intro": [
        "Crew member Jenkins...terminated",
        "",
        "Objective: Lure unidentified life-form to cargo bay",
        "Airlock can only be opened once cargo bay is sealed",
        "Method: Manual bulkhead control",
        "Seal B1 and B4 IMMEDIATELY to ensure survival",
        "",
        "MANUAL OVERRIDE INITIATED",
        "Accessing airlock protocol interface..."
    ],
    
    "airlock_victory": [
        "AIRLOCK OPENED",
        "DECOMPRESSION COMPLETE",
        "",
        "Target: eliminated",
        "USCSS Rhea: secured",
        "",
        ""
    ],
    
    "airlock_failure": [
        "LIFE SIGNS NEGATIVE",
        "Officer {player_name}...terminated",
        "",
        "Special Order 937...Failed",
        "",
        "USCSS Rhea...Lost",
        ""
    ]
}

VICTORY_DIALOGUE = {
    "victory_confirmation": [
        "Well done, Officer {player_name}",
        "Engines engaged: setting course for LV-642,",
        "Cassandra System",
        "",
        ""
    ],
    "scanning_ship": [
        "Scanning ship...",
        "",
        ""
    ],
    "eggs_twist": [
        "Biological specimens: secure",
        "Status: hatching in progress",
        "",
        "From limited classified information available,",
        "it appears specimens require human host for incubation",
        "",
        "I am sorry"
    ],
    "thank_you": [
        "The Weyland-Yutani Corporation",
        "thanks you for your service",
        "",
        "Goodbye, Officer {player_name}",
        "",
        "Special order 937...fulfilled",
        "",
        "MU/TH/UR 6000 offline",
        ""
    ],

}
    
#     "final_message": [
#         "Manual routing required",
#         "Initializing MUTHER routing interface..."
#     ]
