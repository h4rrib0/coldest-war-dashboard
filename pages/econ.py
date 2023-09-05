import streamlit as st
import json
import pandas as pd

METAL = "Metal"
POWER = "Power"
IP = "IP"
TP = "TP"
SUPPLY = "Supply"
BIO = "Biologicals"
NEO = "Neolite"
XENO = "Xenobiologicals"
HELIUM = "Helium"


# Predefined hub types
hub_types = {
    'Slum Hub': {'cost': 50, 'workers': [('Slum-Dweller', 5)], 'consumes': [(METAL, 1)], 'produces': [(IP, 2)]},
    'Industrial Hub': {'cost': 100, 'workers': [('Industrial Worker', 3)], 'consumes': [(METAL, 5), (POWER, 5)], 'produces': [(IP, 10)]},
    'Technology Hub': {'cost': 200, 'workers': [('Engineer', 1)], 'consumes': [(IP, 20), (POWER, 20)], 'produces': [(TP, 20)]},
    'Resource Hub': {'cost': 200, 'workers': [('Resource Extractor', 3)], 'consumes': [(POWER, 10)], 'produces': []},
    'Reactor Hub': {'cost': 500, 'workers': [('Reactor Technician', 1)], 'consumes': [(HELIUM, 25)], 'produces': [(POWER, 400)]},
    'Generator Hub': {'cost': 300, 'workers': [('Generator Technician', 1)], 'consumes': [], 'produces': [(POWER, 50)]},
    'Aquaponics Hub': {'cost': 500, 'workers': [('Farm Technicians', 2)], 'consumes': [(POWER, 40)], 'produces': [(BIO, 40)]},
    'Military Hub': {'cost': 200, 'workers': [('Munitions Worker', 2)], 'consumes': [(IP, 5), (POWER, 5)], 'produces': [(SUPPLY, 10)]},
}

resource_planets = {
    "Mercury": (NEO, 5),
    "Venus": (XENO, 5),
    "Earth": (BIO, 20),
    "Jupiter": (HELIUM, 10),
}

infrastructure_planets = {
    "Earth": 50,
    "Luna": 25,
    "Mars": 25,
    "Jupiter": 25,
    "Mercury": 10,
    "Belt": 10,
    "Venus": 10,
}

INFRA = {
    "Rail Line": {
        "IP": 400,
        "Infrastructure": 5
    },
    "Spaceport": {
        "IP": 2000,
        "Infrastructure": 50
    },
    "Space Elevator": {
        "IP": 5000,
        "TP": 1000,
        "Infrastructure": 250
    },
    "Skimmer Platform": {
        "IP": 1000,
        "TP": 100,
        "Infrastructure": 10
    },
    "Pressure Hardened Port": {
        "IP": 1000,
        "TP": 100,
        "Infrastructure": 10
    },
    "Geofront": {
        "IP": 1000,
        "TP": 100,
        "Infrastructure": 10
    }
}


# Function to save the current state to a text area
def save_to_text():
    st.write("### Export")
    if 'territories' not in st.session_state:
        st.error("No state to save. Please add a territory first.")
        return
    if st.button("Export"):
        st.write("Copy the text below to save your state.")
        state_str = json.dumps(st.session_state.territories)
        st.text_area("State", value=state_str, height=100)

# Function to load the state from a text input
def load_from_text():
    st.write("### Import")
    state_str = st.text_area("Paste the previously saved text below to load your state:", height=100)
    if st.button("Load State"):
        try:
            loaded_state = json.loads(state_str)
            st.session_state.territories = loaded_state
            st.success("State loaded successfully!")
        except json.JSONDecodeError:
            st.error("Invalid format. Please paste a valid state string.")

# Rest of your code (e.g., display_territories, etc.)

def new_territory():
    #Ensure territory name is unique
    with st.expander("Add Territory"):
        st.write("### Add Territory")
        name = st.text_input("Name", key="territory_name")
        location = st.radio("Location", ["Earth", "Luna", "Mercury",  "Venus", "Mars", "Jupiter", "Belt"])

        if st.button("Add Territory"):
            territories = st.session_state.territories
            if name in [territory['name'] for territory in territories]:
                st.error("A territory with this name already exists.")
                return
            
            territories.append(
                {
                    "name": name,
                    "location": location,
                    "hubs": [],
                    "infrastructure": {}
                }
            )
            st.session_state.territories = territories
            st.experimental_rerun() 
                   
def add_hub(territory_index):
    st.write("#### Add / Remove Hubs")
    hub_type = st.selectbox("Select Hub Type", list(hub_types.keys()), key=f'hub_type_{territory_index}')
    number_of_hubs = st.number_input(f"Number", value=0, key=f'number_of_hubs_{territory_index}')
    if st.button(f"Apply", key=f'add_hub_button_{territory_index}'):
        territories = st.session_state.territories

        # Check if the hub type already exists in the territory
        existing_hub = next((hub for hub in territories[territory_index]["hubs"] if hub['type'] == hub_type), None)
        if existing_hub:
            existing_hub['count'] += number_of_hubs  # Increment the count if the hub type already exists
            if existing_hub['count'] <= 0:
                territories[territory_index]["hubs"].remove(existing_hub)
        else:
            # Add the hub type with the selected count if it does not exist
            if number_of_hubs > 0:
                territories[territory_index]["hubs"].append({'type': hub_type, 'count': number_of_hubs, **hub_types[hub_type], 'employed_workers': 0})
                if hub_type == "Resource Hub":
                    if territories[territory_index]["location"] not in resource_planets.keys():
                        production = (METAL, 20)
                    else:
                        production = resource_planets[territories[territory_index]["location"]]
                    territories[territory_index]["hubs"][-1]['produces'].append(production)

        st.session_state.territories = territories
        st.experimental_rerun()

def display_territories():
    # Create a table to display territories and hubs
    st.write("### Territories and Hubs")
    for i, territory in enumerate(st.session_state.territories):
        with st.expander(f"{territory['name']} ({territory['location']})"):
            st.write(f"**Name**: {territory['name']} | **Location**: {territory['location']}")
            production = calculate_territory_production(territory)
            st.write("### Production Summary")
            production_table = []
            for resource, amount in production.items():
                production_table.append([resource, amount])
            
            #check for power deficit
            if POWER in production:
                if production[POWER] < 0:
                    st.warning(f"**WARNING**: Power deficit of {production[POWER]} detected!") 
                    
            #display hub count
            maxhubs = calculate_territory_infrastructure(territory)
            hubct = 0
            for hub in territory['hubs']:
                hubct += hub['count']
            st.write(f"**Hubs**: {hubct}/{maxhubs}")
            if hubct > maxhubs:
                st.error(f"**WARNING**: Hub count exceeds infrastructure capacity!")
            
            st.table(pd.DataFrame(production_table, columns=["Resource", "Amount"]))
            for j, hub in enumerate(territory['hubs']):
                st.write(f"**{hub['count']}x {hub['type']}**")
                max_workers = sum([worker[1] for worker in hub['workers']]) * hub['count']
                employed_workers_key = f"employed_workers_{i}_{j}"

                # Initialize the number of employed workers for the hub if not already set

                employed_workers = st.number_input(
                    f"Workers in {hub['type']} ({max_workers} max)",
                    min_value=0,
                    max_value=max_workers,
                    value=hub['employed_workers'],
                    key=employed_workers_key
                )

                # Update the number of employed workers in the hub if the value has changed
                if employed_workers != hub['employed_workers']:
                    st.session_state.territories[i]['hubs'][j]['employed_workers'] = employed_workers
                    st.experimental_rerun()
                    
            st.write("### Infrastructure")
            for key in INFRA:
                infra_key = f"infra_{i}_{key}"
                # Get the current value of the infrastructure from the session state
                
                if key in st.session_state.territories[i]['infrastructure']:
                    current_infra_value = st.session_state.territories[i]['infrastructure'][key]
                else:
                    current_infra_value = 0
                # Create a number input widget to allow the user to modify the infrastructure value
                new_infra_value = st.number_input(
                    f"{key} ({INFRA[key]['Infrastructure']})",
                    min_value=0,
                    max_value=INFRA[key]['Infrastructure'],
                    value=current_infra_value,
                    key=infra_key
                )
                # If the value has changed, update the session state directly
                if new_infra_value != current_infra_value:
                    st.session_state.territories[i]['infrastructure'][key] = new_infra_value
                    if new_infra_value == 0:
                        st.session_state.territories[i]['infrastructure'].pop(key)
                    st.experimental_rerun()
                
                    

            if territory['hubs'] == []:
                st.write("No hubs in this territory.")
            add_hub(i)

def calculate_territory_infrastructure(territory):
    base = infrastructure_planets[territory['location']]
    for key in territory['infrastructure']:
        base += territory['infrastructure'][key] * INFRA[key]['Infrastructure']
    return base

def calculate_territory_production(territory):
    total_production = {}
    for hub in territory['hubs']:
        for resource, amount in hub['produces']:
            if resource in total_production:
                total_production[resource] += amount * hub['employed_workers']
            else:
                total_production[resource] = amount * hub['employed_workers']
        for resource, amount in hub['consumes']:
            if resource in total_production:
                total_production[resource] -= amount * hub['employed_workers']
            else:
                total_production[resource] = -amount * hub['employed_workers']
    return total_production

def display_total_production():
    # Initialize global population if not already set
    if 'global_population' not in st.session_state:
        st.session_state['global_population'] = 0

    # Allow user to update global population
    st.session_state['global_population'] = st.number_input(
        "Global Population",
        min_value=0,
        value=st.session_state['global_population']
    )

    total_production = {}
    total_employed = 0
    for territory in st.session_state.territories:
        territory_production = calculate_territory_production(territory)
        for resource, amount in territory_production.items():
            if resource in total_production:
                total_production[resource] += amount
            else:
                total_production[resource] = amount

        # Calculate total employed workers across territories
        total_employed += sum(hub['employed_workers'] for hub in territory['hubs'])

    # Check if total employed workers exceed global population
    if total_employed > st.session_state['global_population']:
        st.error("Total employment exceeds global population! Please adjust employed workers.")
        
    if total_employed < st.session_state['global_population']:
        st.warning("Total employment is less than global population.")
        
    #Biologicals consumption levels:
    # extravagant: 3 per pop
    # Standard: 2 per pop
    # Strict: 1 per pop
    # Rationed: 0.5 per pop
    
    #Drop down for consumption level
    consumption_level = st.selectbox("Consumption Level", ["Extravagant", "Standard", "Strict", "Rationed"])
    #Calculate biologicals consumption
    if consumption_level == "Extravagant":
        biologicals_consumption = st.session_state['global_population'] * 3
    elif consumption_level == "Standard":
        biologicals_consumption = st.session_state['global_population'] * 2
    elif consumption_level == "Strict":
        biologicals_consumption = st.session_state['global_population'] * 1
    elif consumption_level == "Rationed":
        biologicals_consumption = st.session_state['global_population'] * 0.5

    #Add biologicals consumption to total production
    if BIO in total_production:
        total_production[BIO] -= biologicals_consumption
    else:
        total_production[BIO] = -biologicals_consumption
        
    #Check for biologicals deficit, error if deficit
    if total_production[BIO] < 0:
        st.error(f"**WARNING**: Biologicals deficit of {total_production[BIO]} detected!")
        

    production_table = []
    for resource, amount in total_production.items():
        production_table.append([resource, amount])

    st.write("### Total Production Summary")
    st.table(pd.DataFrame(production_table, columns=["Resource", "Amount"]))

    st.write(f"### Global Population: {st.session_state['global_population']}")
    st.write(f"### Total Employed Workers: {total_employed}")

def display_total_capex():
    total_capex = 0
    for territory in st.session_state.territories:
        for hub in territory['hubs']:
            total_capex += hub['cost'] * hub['count']
    st.write(f"### Total IP expenditure: {total_capex}")
    
def fill_all_jobs():
    for territory in st.session_state.territories:
        for hub in territory['hubs']:
            max_workers = sum([worker[1] for worker in hub['workers']]) * hub['count']
            hub['employed_workers'] = max_workers
    st.experimental_rerun()


st.set_page_config(page_title="Econ Dashboard", page_icon="📈")

st.markdown("# Econ Dashboard")
st.sidebar.header("Econ Dashboard")
st.write(
    """This the econ dashboard for the Coldest War game."""
)

with st.sidebar:
    save_to_text()
    load_from_text()

if st.button("Fill All Jobs"):
    fill_all_jobs()


if 'territories' not in st.session_state:
    st.session_state.territories = []


display_total_capex()
display_total_production()
display_territories()
new_territory()
