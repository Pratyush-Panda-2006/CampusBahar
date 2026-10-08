"""
Multi-Modal Transit Fare & Route Engine for Bhubaneswar Campuses.
Calculates distance, travel time, and comparative fares across 4 transit modes:
1. 🚌 Mo Bus (CRUT)
2. 🛺 Shared & Reserved Auto
3. 🛵 Bike Taxi (Rapido / Uber Moto)
4. 🚗 Shared Cab (Uber / Ola / InDrive - 4-student split)
"""

import math
from typing import Dict, Any, List

CAMPUS_HUBS: Dict[str, Dict[str, Any]] = {
    "iter": {
        "id": "iter",
        "name": "SOA / ITER University",
        "short_name": "ITER",
        "locality": "Jagamara, Khandagiri",
        "lat": 20.2520,
        "lon": 85.7956,
        "bus_stop": "ITER Main Gate / Jagamara Chhak",
        "auto_stand": "Jagamara Square Auto Stand"
    },
    "kiit": {
        "id": "kiit",
        "name": "KIIT University",
        "short_name": "KIIT",
        "locality": "Patia / Kalarahanga",
        "lat": 20.3540,
        "lon": 85.8184,
        "bus_stop": "KIIT Square / Campus 3 Mo Bus Stop",
        "auto_stand": "Patia Chhak Auto Stand"
    },
    "outr": {
        "id": "outr",
        "name": "OUTR / CET Bhubaneswar",
        "short_name": "OUTR (CET)",
        "locality": "Ghatikia",
        "lat": 20.2764,
        "lon": 85.7725,
        "bus_stop": "Ghatikia Chhak / CET Gate",
        "auto_stand": "Khandagiri Bari Stand"
    },
    "aiims": {
        "id": "aiims",
        "name": "AIIMS Bhubaneswar",
        "short_name": "AIIMS",
        "locality": "Sijua, Patrapada",
        "lat": 20.2312,
        "lon": 85.7738,
        "bus_stop": "AIIMS Main Gate Mo Bus Stop",
        "auto_stand": "Sijua Chhak Auto Stand"
    },
    "utkal": {
        "id": "utkal",
        "name": "Utkal University (Vani Vihar)",
        "short_name": "Utkal Univ",
        "locality": "Vani Vihar / Saheed Nagar",
        "lat": 20.2974,
        "lon": 85.8458,
        "bus_stop": "Vani Vihar NH16 Mo Bus Stop",
        "auto_stand": "Vani Vihar Chhak Auto Stand"
    },
    "silicon": {
        "id": "silicon",
        "name": "Silicon University",
        "short_name": "Silicon",
        "locality": "Infocity, Patia",
        "lat": 20.3582,
        "lon": 85.8123,
        "bus_stop": "Silicon Institute Gate / Infocity Road",
        "auto_stand": "Infocity Chhak Auto Stand"
    },
    "cvraman": {
        "id": "cvraman",
        "name": "CV Raman Global University",
        "short_name": "CV Raman",
        "locality": "Mahura, Janla",
        "lat": 20.2185,
        "lon": 85.7368,
        "bus_stop": "CVRCE Main Gate / Janla Bypass",
        "auto_stand": "Janla Square Auto Stand"
    }
}

DESTINATIONS_DATA: Dict[str, Dict[str, Any]] = {
    "khandagiri": {
        "id": "khandagiri",
        "name": "Khandagiri & Udayagiri Caves",
        "category": "Hills & Caves",
        "locality": "Jagamara-Khandagiri Road",
        "lat": 20.2588,
        "lon": 85.7865,
        "highlights": "Ancient 2nd-century BCE sandstone caves, hill ridge hike, early morning mist",
        "bus_routes": {
            "iter": "Route 11 (5 mins)",
            "kiit": "Route 16 to Fire Station, transfer Route 11 (45 mins)",
            "outr": "Route 11 or direct short auto (10 mins)",
            "aiims": "Route 11 / 23 via Jagamara (15 mins)",
            "utkal": "Route 10 / 11 via Baramunda (30 mins)",
            "silicon": "Route 16 down to Fire Station, transfer Route 11 (50 mins)",
            "cvraman": "Route 24 / Khordha bypass auto (25 mins)"
        }
    },
    "deras": {
        "id": "deras",
        "name": "Deras & Jhumka Dam (Chandaka)",
        "category": "Lakes & Reserves",
        "locality": "Chandaka Wildlife Sanctuary Fringe",
        "lat": 20.3346,
        "lon": 85.7082,
        "highlights": "Eco-walks across earthen dam, dense bamboo forest fringe, calm reservoir breeze",
        "bus_routes": {
            "iter": "Shared auto to Pitapalli/Chandaka, then eco-shuttle (35 mins)",
            "kiit": "Patia-Chandaka road direct bike/auto (30 mins)",
            "outr": "Direct Ghatikia-Chandaka hill road (20 mins)",
            "aiims": "Via Pitapalli bypass towards Chandaka (40 mins)",
            "utkal": "Route 10 to Nayapalli, connect Chandaka road (45 mins)",
            "silicon": "Direct Chandaka link road via Infocity (25 mins)",
            "cvraman": "Via Pitapalli toll gate link (35 mins)"
        }
    },
    "ekamra": {
        "id": "ekamra",
        "name": "Ekamra Kanan Botanical Lake",
        "category": "Lakes & Reserves",
        "locality": "IRC Village, Nayapalli",
        "lat": 20.3060,
        "lon": 85.8118,
        "highlights": "Massive walking perimeter, rose gardens, shaded lawns, pelican wetlands",
        "bus_routes": {
            "iter": "Route 10 direct to Nayapalli IRC Village (20 mins)",
            "kiit": "Route 16 / 10 to Nayapalli (25 mins)",
            "outr": "Route 11 to Baramunda, then Route 10 (25 mins)",
            "aiims": "Route 23 to Nayapalli (30 mins)",
            "utkal": "Direct walk or Route 10 to IRC Village (12 mins)",
            "silicon": "Route 16 to Nayapalli VIP Road (28 mins)",
            "cvraman": "Route 24 via Fire Station to Nayapalli (45 mins)"
        }
    },
    "dhauli": {
        "id": "dhauli",
        "name": "Dhauli Shanti Stupa & Daya Riverbank",
        "category": "Heritage & Culture",
        "locality": "Dhauli Hills, Puri Highway",
        "lat": 20.1923,
        "lon": 85.8394,
        "highlights": "Peaceful white pagoda, open breeze along historical Daya riverbanks, rock edicts",
        "bus_routes": {
            "iter": "Route 20/21 via Kalpana Square towards Puri bypass (40 mins)",
            "kiit": "Route 16 to Master Canteen, then Route 20 (60 mins)",
            "outr": "Route 11 to Master Canteen, then Route 20 (50 mins)",
            "aiims": "Route 23 to Kalpana, transfer Dhauli bus (40 mins)",
            "utkal": "Route 20 from Rasulgarh / Kalpana (35 mins)",
            "silicon": "Route 16 to Master Canteen, connect Route 20 (65 mins)",
            "cvraman": "Via Lingaraj link road towards Puri bypass (45 mins)"
        }
    },
    "nandankanan": {
        "id": "nandankanan",
        "name": "Nandankanan Botanical Garden (Kanjia Lake)",
        "category": "Lakes & Reserves",
        "locality": "Nandankanan Road, Raghunathpur",
        "lat": 20.3995,
        "lon": 85.8252,
        "highlights": "Forest boardwalks, wetlands, birdwatching canopy, fresh freshwater breezes",
        "bus_routes": {
            "iter": "Route 11 to Master Canteen, then Route 16 north to zoo (65 mins)",
            "kiit": "Route 16 direct north along Patia corridor (15 mins)",
            "outr": "Route 11 to Fire Station, connect Route 16 (60 mins)",
            "aiims": "Route 23 to Vani Vihar, transfer Route 16 (70 mins)",
            "utkal": "Route 16 from Vani Vihar direct to Botanical Gate (35 mins)",
            "silicon": "Route 16 direct north from Infocity link (18 mins)",
            "cvraman": "Via Baramunda, transfer Route 16 north (75 mins)"
        }
    },
    "jayadev": {
        "id": "jayadev",
        "name": "Jayadev Vatika Forest Park",
        "category": "Hills & Caves",
        "locality": "Khandagiri Foothills, Jagamara-Khandagiri Road",
        "lat": 20.2644,
        "lon": 85.7834,
        "highlights": "50+ acre landscaped park with forested walking trails, rocks, and streamlets",
        "bus_routes": {
            "iter": "Direct walk or Route 11 / auto (7 mins)",
            "kiit": "Route 16 to Fire Station, transfer auto (40 mins)",
            "outr": "Direct auto along Khandagiri hill road (8 mins)",
            "aiims": "Route 11 or shared auto via Jagamara (15 mins)",
            "utkal": "Route 11 from Baramunda to Khandagiri (30 mins)",
            "silicon": "Route 16 to Fire Station, transfer auto (45 mins)",
            "cvraman": "Route 24 via Janla to Khandagiri foothills (20 mins)"
        }
    },
    "bindusagar": {
        "id": "bindusagar",
        "name": "Bindu Sagar Heritage Corridor",
        "category": "Heritage & Culture",
        "locality": "Old Town, Lingaraj Precinct",
        "lat": 20.2415,
        "lon": 85.8354,
        "highlights": "Sacred lake perimeter stroll, 1,000-year-old temple architecture, peaceful stone ghats",
        "bus_routes": {
            "iter": "Route 20 or direct shared auto via Jagamara-Old Town (20 mins)",
            "kiit": "Route 16 to Master Canteen, connect Route 21 to Old Town (50 mins)",
            "outr": "Route 11 to Jagamara, auto to Old Town (30 mins)",
            "aiims": "Direct auto via Sundarpada road (20 mins)",
            "utkal": "Route 21 from Kalpana Square to Lingaraj (25 mins)",
            "silicon": "Route 16 to Railway Station, connect Route 21 (55 mins)",
            "cvraman": "Via Retang / Sundarpada bypass (30 mins)"
        }
    },
    "ekamrahaat": {
        "id": "ekamrahaat",
        "name": "Ekamra Haat & Native Tree Avenues",
        "category": "Heritage & Culture",
        "locality": "Unit-3, Exhibition Ground Area",
        "lat": 20.2731,
        "lon": 85.8361,
        "highlights": "Open-air craft trails, native tree avenues, Odia culinary stalls, calm garden benches",
        "bus_routes": {
            "iter": "Route 10 or shared auto via Siripur Chhak (18 mins)",
            "kiit": "Route 16 down to Sriya Chhak / Unit-3 (35 mins)",
            "outr": "Route 11 via Fire Station towards AG Square (25 mins)",
            "aiims": "Route 23 to AG Square, short walk (25 mins)",
            "utkal": "Direct short Route 10 / auto down Janpath (15 mins)",
            "silicon": "Route 16 to Master Canteen / Unit-3 (40 mins)",
            "cvraman": "Route 24 to AG Square (35 mins)"
        }
    },
    "barunei": {
        "id": "barunei",
        "name": "Barunei Hill & Perennial Stream",
        "category": "Hills & Caves",
        "locality": "Khordha-Bhubaneswar Border",
        "lat": 20.1804,
        "lon": 85.6698,
        "highlights": "Moderate rocky climb, fresh water perennial springs, dense sal tree canopy",
        "bus_routes": {
            "iter": "Mo Bus Route 24 / Khordha bus to Barunei Gate (35 mins)",
            "kiit": "Route 16 to Master Canteen, transfer Route 24 (75 mins)",
            "outr": "Via Ghatikia bypass to NH16 Khordha (30 mins)",
            "aiims": "Route 24 / NH16 direct auto (22 mins)",
            "utkal": "Route 24 from Vani Vihar along NH16 (50 mins)",
            "silicon": "Route 16 to Baramunda, transfer Route 24 (70 mins)",
            "cvraman": "Direct NH16 link - very close! (15 mins)"
        }
    },
    "kuakhai": {
        "id": "kuakhai",
        "name": "Kuakhai Riverfront & Bali Jatra Grounds",
        "category": "Open Horizons",
        "locality": "Patia-Hanspal Riverbed Corridor",
        "lat": 20.3392,
        "lon": 85.8672,
        "highlights": "Wide open riverbed horizons, sunset breeze, dirt paths, evening sky reflections",
        "bus_routes": {
            "iter": "Route 11 to Rasulgarh, connect Hanspal link (40 mins)",
            "kiit": "Direct short bike/auto east towards river bank (15 mins)",
            "outr": "Route 11 to Baramunda, connect NH16 to Hanspal (45 mins)",
            "aiims": "Via Bypass to Rasulgarh and Hanspal (40 mins)",
            "utkal": "Route 10 / auto straight down to Kuakhai bridge (15 mins)",
            "silicon": "Direct eastward link to Kuakhai riverbank (18 mins)",
            "cvraman": "Via NH16 corridor to Hanspal (50 mins)"
        }
    },
    "sisupalgarh": {
        "id": "sisupalgarh",
        "name": "Sisupalgarh Fortified Ancient Ruins",
        "category": "Heritage & Culture",
        "locality": "Sisupalgarh, Puri Bypass",
        "lat": 20.2378,
        "lon": 85.8601,
        "highlights": "2,500-year-old fortified ramparts, monolithic stone pillars, quiet sunset horizon walks",
        "bus_routes": {
            "iter": "Shared auto via Sundarpada / Old Town to Sisupalgarh (25 mins)",
            "kiit": "Route 16 to Kalpana Square, short auto (45 mins)",
            "outr": "Route 11 to Master Canteen, connect Kalpana auto (40 mins)",
            "aiims": "Via Sundarpada bypass road direct auto (25 mins)",
            "utkal": "Route 20/21 from Kalpana Square (25 mins)",
            "silicon": "Route 16 to Kalpana Square, transfer auto (50 mins)",
            "cvraman": "Via Sundarpada-Jatni bypass road (35 mins)"
        }
    },
    "lingaraj": {
        "id": "lingaraj",
        "name": "Lingaraj Temple & Ekamra Kshetra Heritage Circuit",
        "category": "Heritage & Culture",
        "locality": "Old Town Sacred Core",
        "lat": 20.2382,
        "lon": 85.8336,
        "highlights": "11th-century Kalinga sandstone tower, ancient sacred courtyards, holy silence",
        "bus_routes": {
            "iter": "Route 20 or direct shared auto via Jagamara (20 mins)",
            "kiit": "Route 16 to Master Canteen, transfer Route 21 (45 mins)",
            "outr": "Route 11 to Jagamara, auto to Lingaraj (25 mins)",
            "aiims": "Direct auto via Sundarpada link (18 mins)",
            "utkal": "Route 21 from Kalpana Square straight to temple (20 mins)",
            "silicon": "Route 16 to Railway Station, transfer Route 21 (50 mins)",
            "cvraman": "Via Retang / Sundarpada link (30 mins)"
        }
    },
    "chausathi": {
        "id": "chausathi",
        "name": "Chausathi Yogini Temple & Enclosure (Hirapur)",
        "category": "Heritage & Culture",
        "locality": "Hirapur Village, Daya Riverbank",
        "lat": 20.2289,
        "lon": 85.8778,
        "highlights": "Rare 9th-century open-air circular hypaethral shrine overlooking peaceful paddy fields",
        "bus_routes": {
            "iter": "Via Old Town towards Hirapur rural link road (35 mins)",
            "kiit": "Via Rasulgarh and Daya river bypass (45 mins)",
            "outr": "Route 11 to Kalpana, rural auto to Hirapur (45 mins)",
            "aiims": "Via Sundarpada / Puri bypass (35 mins)",
            "utkal": "Via Rasulgarh down towards Hirapur road (30 mins)",
            "silicon": "Via NH16 to Rasulgarh, connect Hirapur (50 mins)",
            "cvraman": "Via Retang and Puri bypass (40 mins)"
        }
    },
    "rprc": {
        "id": "rprc",
        "name": "Regional Plant Resource Centre (Cactus Garden)",
        "category": "Lakes & Reserves",
        "locality": "IRC Village, Nayapalli",
        "lat": 20.3015,
        "lon": 85.8080,
        "highlights": "Asia's largest cactus conservatory, lakeside walking perimeter, shaded bamboo groves",
        "bus_routes": {
            "iter": "Route 10 to Nayapalli IRC Village stop (18 mins)",
            "kiit": "Route 16 / 10 to Nayapalli (25 mins)",
            "outr": "Route 11 to Baramunda, Route 10 to RPRC (20 mins)",
            "aiims": "Route 23 to Nayapalli (28 mins)",
            "utkal": "Route 10 straight from Vani Vihar (15 mins)",
            "silicon": "Route 16 to Nayapalli VIP Road (25 mins)",
            "cvraman": "Route 24 via Fire Station to Nayapalli (40 mins)"
        }
    },
    "atri": {
        "id": "atri",
        "name": "Atri Hot Sulphur Springs & Nature Walk",
        "category": "Hills & Caves",
        "locality": "Baghamari, Khordha District",
        "lat": 20.2030,
        "lon": 85.5020,
        "highlights": "Natural bubbling thermal springs, countryside mango orchards, healing mineral waters",
        "bus_routes": {
            "iter": "Mo Bus / Khordha bus to Baghamari (55 mins)",
            "kiit": "Route 16 to Master Canteen, express to Khordha-Atri (85 mins)",
            "outr": "Via Ghatikia NH16 to Khordha Baghamari (50 mins)",
            "aiims": "Direct NH16 Khordha bus towards Baghamari (45 mins)",
            "utkal": "Route 24 to Khordha, connecting local bus to Atri (65 mins)",
            "silicon": "Route 16 to Baramunda, Khordha bus (80 mins)",
            "cvraman": "Direct NH16 link from Janla (35 mins)"
        }
    },
    "mukteswara": {
        "id": "mukteswara",
        "name": "Mukteswara & Parasurameswara Temples",
        "category": "Heritage & Culture",
        "locality": "Old Town, Kedar Gouri Road",
        "lat": 20.2432,
        "lon": 85.8339,
        "highlights": "10th-century Kalinga torana archway, peaceful temple courtyard, Marichi Kunda sacred tank paths",
        "bus_routes": {
            "iter": "Route 20 or shared auto via Jagamara Chhak (18 mins)",
            "kiit": "Route 16 to Master Canteen, connect Route 21 to Old Town (40 mins)",
            "outr": "Route 11 to Jagamara, auto to Old Town (20 mins)",
            "aiims": "Direct shared auto via Sundarpada (18 mins)",
            "utkal": "Route 21 from Kalpana Square (20 mins)",
            "silicon": "Route 16 to Master Canteen, connect Route 21 (45 mins)",
            "cvraman": "Via Retang / Sundarpada link road (28 mins)"
        }
    },
    "tribal": {
        "id": "tribal",
        "name": "Museum of Tribal Arts & Artifacts",
        "category": "Heritage & Culture",
        "locality": "CRPF Square, Unit-8, Nayapalli Road",
        "lat": 20.2831,
        "lon": 85.8145,
        "highlights": "Authentic full-scale tribal village dwellings, shaded green canopies, open-air cultural trails",
        "bus_routes": {
            "iter": "Direct shared auto via Siripur to CRPF Square (12 mins)",
            "kiit": "Route 16 / 10 to CRPF Chhak (20 mins)",
            "outr": "Route 11 to Fire Station, connect auto to CRPF (15 mins)",
            "aiims": "Route 23 to CRPF Square (22 mins)",
            "utkal": "Route 10 straight from Vani Vihar to CRPF (14 mins)",
            "silicon": "Route 16 down to CRPF Square (22 mins)",
            "cvraman": "Route 24 via Fire Station to CRPF Chhak (30 mins)"
        }
    },
    "kalabhoomi": {
        "id": "kalabhoomi",
        "name": "Odisha Crafts Museum - Kala Bhoomi",
        "category": "Heritage & Culture",
        "locality": "Pokhariput, Gandamunda",
        "lat": 20.2396,
        "lon": 85.8023,
        "highlights": "12-acre terracotta courtyards, live artisan workshops, lotus waterbodies, breezy outdoor verandas",
        "bus_routes": {
            "iter": "Short auto or walk down Jagamara-Pokhariput road (6 mins)",
            "kiit": "Route 16 to Master Canteen, connect Pokhariput auto (45 mins)",
            "outr": "Direct auto via Khandagiri-Pokhariput bypass (12 mins)",
            "aiims": "Shared auto along Sijua-Pokhariput road (10 mins)",
            "utkal": "Route 21 to Airport / Pokhariput (25 mins)",
            "silicon": "Route 16 to Master Canteen, transfer auto (50 mins)",
            "cvraman": "Via Retang-Jatni-Pokhariput bypass (20 mins)"
        }
    }
}


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points in km."""
    R = 6371.0  # Earth's radius in kilometers
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    direct_dist = R * c
    # Road tortuosity factor: real roads in Bhubaneswar are ~1.28x line-of-sight
    return round(direct_dist * 1.28, 1)


def compute_transit_matrix(origin_campus_id: str, destination_id: str) -> Dict[str, Any]:
    """
    Computes accurate routes, times, and student fare matrices from origin campus to destination.
    Returns:
      - distance_km
      - modes: Mo Bus, Shared Auto, Bike Taxi, Shared Cab (with split)
      - map_links: embed_url, directions_url
    """
    campus = CAMPUS_HUBS.get(origin_campus_id.lower(), CAMPUS_HUBS["iter"])
    destination = DESTINATIONS_DATA.get(destination_id.lower(), DESTINATIONS_DATA["khandagiri"])

    dist_km = haversine_distance_km(
        campus["lat"], campus["lon"],
        destination["lat"], destination["lon"]
    )
    # Ensure minimum 1.5 km
    dist_km = max(1.5, dist_km)

    # 1. Mo Bus (CRUT)
    bus_spec = destination.get("bus_routes", {}).get(campus["id"], "Mo Bus Connected")
    if dist_km <= 5.0:
        bus_fare = "₹10"
        bus_time = f"{max(10, int(dist_km * 3.5))} mins"
    elif dist_km <= 12.0:
        bus_fare = "₹15 – ₹20"
        bus_time = f"{int(dist_km * 3.2)} mins"
    else:
        bus_fare = "₹25 – ₹30"
        bus_time = f"{int(dist_km * 3.0)} mins"

    # 2. Shared & Reserved Auto
    shared_fare = f"₹{min(35, max(15, int(dist_km * 2.2)))} / seat"
    private_auto_min = int(40 + dist_km * 11)
    private_auto_max = int(55 + dist_km * 14)
    auto_time = f"{max(8, int(dist_km * 2.4))} mins"

    # 3. Bike Taxi (Rapido / Uber Moto)
    bike_min = int(25 + dist_km * 8)
    bike_max = int(35 + dist_km * 10)
    bike_time = f"{max(6, int(dist_km * 1.8))} mins"

    # 4. Shared Cab (Uber / Ola / InDrive - 4-student carpool)
    cab_min = int(90 + dist_km * 14)
    cab_max = int(120 + dist_km * 18)
    split_min = int(cab_min / 4)
    split_max = int(cab_max / 4)
    cab_time = f"{max(10, int(dist_km * 2.0))} mins"

    # Google Maps URL generation
    embed_url = f"https://www.google.com/maps?q={destination['lat']},{destination['lon']}&z=14&output=embed"
    directions_url = (
        f"https://www.google.com/maps/dir/?api=1&origin={campus['lat']},{campus['lon']}"
        f"&destination={destination['lat']},{destination['lon']}&travelmode=transit"
    )

    return {
        "origin_campus": {
            "id": campus["id"],
            "name": campus["name"],
            "short_name": campus["short_name"],
            "locality": campus["locality"],
            "bus_stop": campus["bus_stop"],
            "auto_stand": campus["auto_stand"]
        },
        "destination": {
            "id": destination["id"],
            "name": destination["name"],
            "category": destination["category"],
            "locality": destination["locality"],
            "highlights": destination["highlights"]
        },
        "distance_km": dist_km,
        "modes": [
            {
                "id": "mobus",
                "name": "Mo Bus (CRUT)",
                "icon": "🚌",
                "route_info": bus_spec,
                "boarding": campus["bus_stop"],
                "est_time": bus_time,
                "cost_label": bus_fare,
                "badge": "Cheapest / AC",
                "badge_color": "var(--teal)"
            },
            {
                "id": "auto",
                "name": "Shared & Reserved Auto",
                "icon": "🛺",
                "route_info": f"Shared: {shared_fare} | Private: ₹{private_auto_min}–₹{private_auto_max}",
                "boarding": campus["auto_stand"],
                "est_time": auto_time,
                "cost_label": f"₹{private_auto_min}–₹{private_auto_max}",
                "badge": "Zero Wait Time",
                "badge_color": "var(--coral)"
            },
            {
                "id": "biketaxi",
                "name": "Bike Taxi (Rapido)",
                "icon": "🛵",
                "route_info": "Doorstep pickup via app",
                "boarding": "Hostel Gate Entrance",
                "est_time": bike_time,
                "cost_label": f"₹{bike_min}–₹{bike_max}",
                "badge": "Fastest in Traffic",
                "badge_color": "var(--mustard)"
            },
            {
                "id": "cab",
                "name": "Shared Cab (4-Student Split)",
                "icon": "🚗",
                "route_info": f"Total ₹{cab_min}–₹{cab_max} (₹{split_min}–₹{split_max}/person)",
                "boarding": "Campus Gate Pick-up",
                "est_time": cab_time,
                "cost_label": f"₹{split_min}–₹{split_max} / person",
                "badge": "Best for Groups",
                "badge_color": "var(--violet)"
            }
        ],
        "maps": {
            "embed_url": embed_url,
            "directions_url": directions_url
        }
    }
