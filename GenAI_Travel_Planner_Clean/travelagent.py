import json
import os
import re
import requests
import googlemaps
from amadeus import Client, ResponseError
from serpapi import GoogleSearch
from agno.agent import Agent
from agno.tools.serpapi import SerpApiTools
from agno.models.google import Gemini
from datetime import datetime
from config import config

# Initialize session state to keep travel plan visible
if 'plan_generated' not in st.session_state:
    st.session_state.plan_generated = False

def verify_website(url, timeout=3):
    """Check if a website URL is accessible"""
    if not url or url == '#' or 'google.com/maps' in url:
        return None
    try:
        if not url.startswith(('http://', 'https://')):
            url = 'https://' + url
        response = requests.head(url, timeout=timeout, allow_redirects=True)
        return url if response.status_code < 400 else None
    except:
        return None

def get_maps_link(name, address=""):
    """Generate Google Maps link for a location"""
    query = f"{name} {address}".strip().replace(' ', '+')
    return f"https://www.google.com/maps/search/{query}"

# Validate API keys and show setup instructions if needed
if not config.validate_required_keys()[0]:
    config.display_setup_instructions()
    st.stop()

# Set environment variables for libraries that need them
os.environ["GOOGLE_API_KEY"] = config.GOOGLE_API_KEY

# Initialize API clients
gmaps = googlemaps.Client(key=config.GOOGLE_PLACES_API_KEY)

# Initialize Amadeus client for production
amadeus = Client(
    client_id=config.AMADEUS_CLIENT_ID,
    client_secret=config.AMADEUS_CLIENT_SECRET,
    hostname='production'  # Uses api.amadeus.com for production (real flight data)
)

def test_amadeus_connection():
    """Test Amadeus production API connection"""
    try:
        # Simple test to verify production API is working
        response = amadeus.reference_data.locations.get(keyword='NYC', subType='AIRPORT')
        if response.data:
            return True
        return False
    except Exception as e:
        return False

# Test connection on startup
if 'amadeus_tested' not in st.session_state:
    st.session_state.amadeus_tested = test_amadeus_connection()

# Custom CSS for Black, White & Mustard Theme
st.markdown("""
<style>
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700&display=swap');
    
    /* Main background and text */
    .stApp {
        background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
        color: #ffffff;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Header styling */
    .main-header {
        background: #1a1a1a;
        border: 2px solid #D4AF37;
        padding: 2rem;
        border-radius: 15px;
        margin-bottom: 2rem;
        text-align: center;
        box-shadow: 0 8px 32px rgba(212, 175, 55, 0.3);
    }
    
    .main-header h1 {
        color: #1a1a1a;
        font-weight: 700;
        font-size: 3rem;
        margin: 0;
        text-shadow: 2px 2px 4px rgba(0,0,0,0.1);
    }
    
    .main-header p {
        color: #2d2d2d;
        font-size: 1.2rem;
        margin: 0.5rem 0 0 0;
        font-weight: 500;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #2d2d2d 0%, #1a1a1a 100%);
        border-right: 3px solid #D4AF37;
    }
    
    /* Input fields */
    .stTextInput > div > div > input,
    .stSelectbox > div > div > select,
    .stDateInput > div > div > input,
    .stNumberInput > div > div > input {
        background-color: #2d2d2d;
        color: #ffffff;
        border: 2px solid #D4AF37;
        border-radius: 10px;
        padding: 0.5rem;
        font-family: 'Poppins', sans-serif;
    }
    
    .stTextInput > div > div > input:focus,
    .stSelectbox > div > div > select:focus,
    .stDateInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #F4D03F;
        box-shadow: 0 0 10px rgba(212, 175, 55, 0.5);
    }
    
    /* Buttons */
    .stButton > button {
        background: linear-gradient(45deg, #D4AF37 0%, #F4D03F 100%);
        color: #1a1a1a;
        border: none;
        border-radius: 25px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-family: 'Poppins', sans-serif;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
    }
    
    .stButton > button:hover {
        background: linear-gradient(45deg, #F4D03F 0%, #D4AF37 100%);
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
    }
    
    /* Enhanced Radio Button Styling */
    .stRadio > div {
        background: rgba(45, 45, 45, 0.5);
        border-radius: 8px;
        padding: 0.5rem;
        margin: 0.3rem 0;
    }
    
    .stRadio > div > label {
        background: linear-gradient(135deg, #2d2d2d 0%, #3a3a3a 100%);
        border: 2px solid #D4AF37;
        border-radius: 8px;
        padding: 0.6rem 1rem;
        margin: 0.2rem 0;
        display: block;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 3px 10px rgba(0, 0, 0, 0.2);
        font-size: 0.9rem;
    }
    
    .stRadio > div > label:hover {
        background: linear-gradient(135deg, #3a3a3a 0%, #4a4a4a 100%);
        border-color: #F4D03F;
        transform: translateY(-1px);
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
    }
    
    .stRadio > div > label[data-checked="true"] {
        background: linear-gradient(135deg, #D4AF37 0%, #F4D03F 100%);
        color: #1a1a1a;
        border-color: #F4D03F;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
    }
    
    /* Radio button text styling */
    .stRadio label {
        color: #F4D03F !important;
        font-weight: 500;
        font-size: 0.9rem;
    }
    
    /* Cards and containers */
    .flight-card, .hotel-card, .restaurant-card, .activity-card {
        background: #1a1a1a;
        border: 2px solid #D4AF37;
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1rem 0;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
    }
    
    .flight-card:hover, .hotel-card:hover, .restaurant-card:hover, .activity-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(212, 175, 55, 0.2);
        border-color: #F4D03F;
    }
    
    /* Section headers */
    .section-header {
        background: linear-gradient(90deg, #D4AF37 0%, #F4D03F 100%);
        color: #1a1a1a;
        padding: 1rem 2rem;
        border-radius: 10px;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
        font-size: 1.3rem;
        text-align: center;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
    }
    
    /* Metrics and info boxes */
    .stMetric {
        background: #2d2d2d;
        border: 1px solid #D4AF37;
        border-radius: 10px;
        padding: 1rem;
    }
    
    /* Expander styling */
    .streamlit-expanderHeader {
        background: linear-gradient(90deg, #D4AF37 0%, #F4D03F 100%);
        color: #1a1a1a;
        border-radius: 10px;
        font-weight: 600;
    }
    
    .streamlit-expanderContent {
        background: #2d2d2d;
        border: 1px solid #D4AF37;
        border-radius: 0 0 10px 10px;
    }
    
    /* Success/Info messages */
    .stSuccess {
        background: linear-gradient(90deg, #D4AF37 0%, #F4D03F 100%);
        color: #1a1a1a;
        border-radius: 10px;
    }
    
    /* Labels and text */
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #D4AF37;
        font-family: 'Poppins', sans-serif;
    }
    
    label {
        color: #F4D03F !important;
        font-weight: 500;
        font-family: 'Poppins', sans-serif;
    }
    
    /* Price highlighting */
    .price-highlight {
        background: linear-gradient(45deg, #D4AF37, #F4D03F);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-weight: 700;
        font-size: 1.2rem;
    }
    
    /* Loading animation */
    .stSpinner {
        border-color: #D4AF37 !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: #1a1a1a;
    }
    
    ::-webkit-scrollbar-thumb {
        background: #D4AF37;
        border-radius: 4px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: #F4D03F;
    }
    
    /* Custom animations */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .fade-in {
        animation: fadeInUp 0.6s ease-out;
    }
    
    /* Mobile responsiveness */
    @media (max-width: 768px) {
        .main-header h1 {
            font-size: 2rem;
        }
        
        .main-header p {
            font-size: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# Production mode detection - simplified for production use
def is_production_mode():
    """Always return True for production environment"""
    return True

def should_use_google_places():
    """Always use Google Places API when available"""
    return config.GOOGLE_PLACES_API_KEY and not config.GOOGLE_PLACES_API_KEY.startswith("#")

def should_use_amadeus():
    """Always use Amadeus API when available"""
    return config.AMADEUS_CLIENT_ID and config.AMADEUS_CLIENT_SECRET

# Airport coordinates helper for car rentals
def get_airport_coordinates(iata_code):
    """Get coordinates for major airports"""
    airport_coords = {
        'JNB': {'lat': -26.1367, 'lng': 28.2411},  # Johannesburg O.R. Tambo
        'CPT': {'lat': -33.9715, 'lng': 18.6021},  # Cape Town International
        'DUR': {'lat': -29.6144, 'lng': 31.1197},  # Durban King Shaka
        'LHR': {'lat': 51.4700, 'lng': -0.4543},   # London Heathrow
        'JFK': {'lat': 40.6413, 'lng': -73.7781},  # New York JFK
        'LAX': {'lat': 33.9425, 'lng': -118.4081}, # Los Angeles LAX
        'CDG': {'lat': 49.0097, 'lng': 2.5479},    # Paris Charles de Gaulle
        'NRT': {'lat': 35.7720, 'lng': 140.3929},  # Tokyo Narita
        'SYD': {'lat': -33.9399, 'lng': 151.1753}, # Sydney Kingsford Smith
        'PLZ': {'lat': -33.9850, 'lng': 25.6173},  # Port Elizabeth
        'BFN': {'lat': -29.0927, 'lng': 26.3023},  # Bloemfontein
        'ELS': {'lat': -33.0356, 'lng': 27.8258},  # East London
        'GRJ': {'lat': -34.0056, 'lng': 22.3789},  # George
        'KIM': {'lat': -28.8028, 'lng': 24.7651},  # Kimberley
        'UTN': {'lat': -28.3991, 'lng': 21.2606},  # Upington
        'PTG': {'lat': -23.9261, 'lng': 29.4584},  # Polokwane
        'MQP': {'lat': -25.3832, 'lng': 31.1056}   # Nelspruit
    }
    return airport_coords.get(iata_code, {'lat': 0, 'lng': 0})

# Main Header with Custom Styling
st.markdown("""
<div class="main-header fade-in">
    <h1 style="color: #ffffff; margin: 0; font-weight: 700; font-size: 3rem; text-shadow: 2px 2px 4px rgba(0,0,0,0.5);">🌍 Revgrowth Travel Planner</h1>
    <p style="color: #D4AF37; font-size: 1.2rem; margin: 0.5rem 0 0 0; font-weight: 500;">Discover • Plan • Experience | Your Dream Journey Awaits</p>
</div>
""", unsafe_allow_html=True)

# Prepare city-country options for dropdowns
# Prepare city-country options for dropdowns
# Code cleaned up - removed development mode toggle
# Code cleaned up - production ready

# Prepare city-country options for dropdowns
CITY_TO_IATA = {
    "Mumbai, India": "BOM",
    "Delhi, India": "DEL",
    "Durban, South Africa": "DUR",
    "Johannesburg, South Africa": "JNB",
    "London, United Kingdom": "LHR",
    "New York, Usa": "JFK",
    "Paris, France": "CDG",
    "Tokyo, Japan": "HND",
    "Cape Town, South Africa": "CPT",
    "Port Elizabeth, South Africa": "PLZ",
    "Bloemfontein, South Africa": "BFN",
    "East London, South Africa": "ELS",
    "George, South Africa": "GRJ",
    "Kimberley, South Africa": "KIM",
    "Upington, South Africa": "UTN",
    "Pietermaritzburg, South Africa": "PZB",
    "Polokwane, South Africa": "PTG",
    "Nelspruit, South Africa": "MQP"
}

# Simpler get_iata_code function
def get_iata_code(city_country):
    """Get IATA code from city-country string"""
    result = CITY_TO_IATA.get(city_country, None)
    
    if result:
        return result
    else:
        # If not found, generate a 3-letter code from the city name
        city_clean = city_country.split(',')[0].strip().replace(' ', '')[:3].upper()
        return city_clean

city_options = list(CITY_TO_IATA.keys())

# Main Application Logic with State Persistence
def main_app():
    """Main application with persistent state management"""
    
    # Check if we should show the travel plan or the form
    if st.session_state.travel_plan_generated and st.session_state.travel_plan_data:
        show_travel_plan()
    else:
        show_travel_form()

def show_travel_form():
    """Display the travel planning form"""
    # User Inputs Section
    st.markdown('<div class="section-header">🌍 Where are you headed?</div>', unsafe_allow_html=True)
    
    # Use session state to preserve form values
    source = st.selectbox(
        "🛫 Departure City (City, Country):", 
        city_options, 
        index=city_options.index(st.session_state.form_data.get('source', "Durban, South Africa")) if st.session_state.form_data.get('source', "Durban, South Africa") in city_options else 0,
        key='source_input'
    )
    destination = st.selectbox(
        "🛬 Destination (City, Country):", 
        city_options, 
        index=city_options.index(st.session_state.form_data.get('destination', "Johannesburg, South Africa")) if st.session_state.form_data.get('destination', "Johannesburg, South Africa") in city_options else 1,
        key='destination_input'
    )

    travel_theme = st.selectbox(
        "🎭 Select Your Travel Theme:",
        ["💼 Business Trip", "💑 Couple Getaway", "👨‍👩‍👧‍👦 Family Vacation", "🏔️ Adventure Trip", "🧳 Solo Exploration"],
        index=0,
        key='theme_input'
    )

    # Divider for aesthetics
    st.markdown("---")

    st.markdown(
        f"""
        <div class="flight-card fade-in" style="text-align: center; margin: 2rem 0;">
            <h3 style="color: #ffffff; margin-bottom: 1rem;">🌟 Your {travel_theme} to {destination} is about to begin! 🌟</h3>
            <p style="color: #D4AF37; font-size: 1.1rem;">Let's find the best flights, car rentals, and experiences for your unforgettable journey.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    activity_preferences = st.text_area(
        "🌍 What activities do you enjoy? (e.g., relaxing on the beach, exploring historical sites, nightlife, adventure)",
        value=st.session_state.form_data.get('activities', ""),
        placeholder="Type your preferred activities here...",
        key='activities_input'
    )

    departure_date = st.date_input("📅 Departure Date", key='departure_date_input')

    # Smaller departure time preference underneath
    departure_time_pref = st.selectbox(
        "🛫 Time Preference:",
        ["🌅 Morning (06:00-12:00)", "☀️ Afternoon (12:00-18:00)", "🌙 Evening (18:00-00:00)", "🦉 Late Night (00:00-06:00)", "⏰ Any Time"],
        index=4,  # Default to "Any Time"
        help="Preferred departure time window",
        key='departure_time_input'
    )

    return_date = st.date_input("📅 Return Date", key='return_date_input')

    # Smaller return time preference underneath
    return_time_pref = st.selectbox(
        "🛬 Time Preference:",
        ["🌅 Morning (06:00-12:00)", "☀️ Afternoon (12:00-18:00)", "🌙 Evening (18:00-00:00)", "🦉 Late Night (00:00-06:00)", "⏰ Any Time"],
        index=4,  # Default to "Any Time"
        help="Preferred return time window",
        key='return_time_input'
    )

    # Number of travelers slider
    num_travelers = st.slider(
        "👥 Number of Travelers:",
        min_value=1,
        max_value=10,
        value=st.session_state.form_data.get('travelers', 1),
        step=1,
        help="Select how many people will be traveling",
        key='travelers_input'
    )

    # Store form data in session state
    st.session_state.form_data.update({
        'source': source,
        'destination': destination,
        'travel_theme': travel_theme,
        'activities': activity_preferences,
        'departure_date': departure_date,
        'departure_time_pref': departure_time_pref,
        'return_date': return_date,
        'return_time_pref': return_time_pref,
        'travelers': num_travelers
    })

def show_travel_plan():
    """Display the generated travel plan with action buttons"""
    
    # Action buttons at the top
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("🔄 Generate New Plan", type="primary"):
            # Reset state to show form again
            st.session_state.travel_plan_generated = False
            st.session_state.travel_plan_data = None
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Page"):
            # Full page refresh
            st.rerun()
    
    # Display the travel plan data
    if st.session_state.travel_plan_data:
        st.markdown("---")
        
        # Display saved travel plan
        plan_data = st.session_state.travel_plan_data
        
        # Show trip summary
        if 'trip_summary' in plan_data:
            st.markdown(f"""
            <div class="flight-card fade-in" style="text-align: center; margin: 2rem 0;">
                <h2 style="color: #ffffff; margin-bottom: 1rem;">🌟 Your {plan_data.get('travel_theme', 'Trip')} to {plan_data.get('destination', 'destination')} 🌟</h2>
                <p style="color: #ffffff; font-size: 1.1rem;">{plan_data['trip_summary']}</p>
            </div>
            """, unsafe_allow_html=True)
        
        # Display flights section
        if 'flights' in plan_data and plan_data['flights']:
            st.subheader("✈️ Flight Options")
            for flight in plan_data['flights']:
                display_flight_card(flight)
        
        # Display car rental section
        if 'car_rental_url' in plan_data:
            st.subheader("🚗 Car Rental Booking")
            st.markdown(f"""
            ### 🎯 Ready to Book Your Car Rental?
            
            **📍 Pickup Location:** {plan_data.get('destination', 'destination')}  
            **📅 Rental Period:** {plan_data.get('departure_date', 'N/A')} - {plan_data.get('return_date', 'N/A')}  
            **👥 Travelers:** {plan_data.get('travelers', 1)}
            
            ### 🌟 **[Find & Book Your Car Rental on Skyscanner]({plan_data['car_rental_url']})**
            
            *Click the link above to compare all available rental cars and book directly with your preferred provider.*
            """)
        
        # Display restaurants section
        if 'restaurants' in plan_data and plan_data['restaurants']:
            st.subheader("🍽️ Restaurant Recommendations")
            display_restaurant_recommendations(plan_data['restaurants'])

def display_flight_card(flight):
    """Display a single flight card"""
    # Implementation for flight card display
    pass

def display_restaurant_recommendations(restaurants):
    """Display restaurant recommendations with verified links"""
    with st.expander(f"🍽️ View All {len(restaurants)} Restaurant Recommendations"):
        for idx, restaurant in enumerate(restaurants, 1):
            restaurant_name = restaurant.get('name', 'Unknown Restaurant')
            address = restaurant.get('address', 'Address not available')
            phone = restaurant.get('phone', 'Phone not available')
            website = restaurant.get('website', '#')
            rating = restaurant.get('rating', 'N/A')
            
            # Verify website URL and use Google Maps as fallback
            verified_website = verify_website(website)
            maps_link = get_maps_link(restaurant_name, address)
            
            # Display restaurant info
            st.markdown(f"""
            **{idx}. {restaurant_name}**
            - 📍 **Address:** {address}
            - ⭐ **Rating:** {rating}
            - 📞 **Phone:** {phone}
            - 🌐 **Website:** {f'[Visit Website]({verified_website})' if verified_website else 'Website not available'}
            - 🗺️ **[Find on Google Maps]({maps_link})**
            """)
            st.markdown("---")

# User Inputs Section
st.markdown("""
<div style="
    background: #1a1a1a;
    border: 2px solid #D4AF37;
    padding: 1.5rem;
    border-radius: 15px;
    margin: 2rem 0;
    text-align: center;
    box-shadow: 0 8px 32px rgba(212, 175, 55, 0.3);
">
    <h2 style="color: #ffffff; margin: 0; font-weight: 700; font-size: 2rem;">🌍 Where are you headed?</h2>
    <p style="color: #D4AF37; margin: 0.5rem 0 0 0; font-weight: 500; font-size: 1rem;">Select your perfect travel destinations</p>
</div>
""", unsafe_allow_html=True)
source = st.selectbox(
    "🛫 Departure City (City, Country):", 
    city_options, 
    index=city_options.index("Durban, South Africa") if "Durban, South Africa" in city_options else 0
)
destination = st.selectbox(
    "🛬 Destination (City, Country):", 
    city_options, 
    index=city_options.index("Johannesburg, South Africa") if "Johannesburg, South Africa" in city_options else 1
)

travel_theme = st.selectbox(
    "🎭 Select Your Travel Theme:",
    ["💼 Business Trip", "💑 Couple Getaway", "👨‍👩‍👧‍👦 Family Vacation", "🏔️ Adventure Trip", "🧳 Solo Exploration"]
)

# Divider for aesthetics
st.markdown("---")

st.markdown(
    f"""
    <div class="flight-card fade-in" style="text-align: center; margin: 2rem 0;">
        <h3 style="color: #ffffff; margin-bottom: 1rem;">🌟 Your {travel_theme} to {destination} is about to begin! 🌟</h3>
        <p style="color: #D4AF37; font-size: 1.1rem;">Let's find the best flights, car rentals, and experiences for your unforgettable journey.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

def format_datetime(iso_string):
    try:
        dt = datetime.strptime(iso_string, "%Y-%m-%d %H:%M")
        return dt.strftime("%b-%d, %Y | %I:%M %p")  # Example: Mar-06, 2025 | 6:20 PM
    except:
        return "N/A"

activity_preferences = st.text_area(
    "🌍 What activities do you enjoy? (e.g., relaxing on the beach, exploring historical sites, nightlife, adventure)",
    value="",
    placeholder="Type your preferred activities here..."
)

departure_date = st.date_input("📅 Departure Date")

# Smaller departure time preference underneath
departure_time_pref = st.selectbox(
    "🛫 Time Preference:",
    ["🌅 Morning (06:00-12:00)", "☀️ Afternoon (12:00-18:00)", "🌙 Evening (18:00-00:00)", "🦉 Late Night (00:00-06:00)", "⏰ Any Time"],
    index=4,  # Default to "Any Time"
    help="Preferred departure time window"
)

return_date = st.date_input("📅 Return Date")

# Smaller return time preference underneath
return_time_pref = st.selectbox(
    "🛬 Time Preference:",
    ["🌅 Morning (06:00-12:00)", "☀️ Afternoon (12:00-18:00)", "🌙 Evening (18:00-00:00)", "🦉 Late Night (00:00-06:00)", "⏰ Any Time"],
    index=4,  # Default to "Any Time"
    help="Preferred return time window"
)

# Number of travelers slider
num_travelers = st.slider(
    "👥 Number of Travelers:",
    min_value=1,
    max_value=10,
    value=1,
    step=1,
    help="Select how many people will be traveling"
)

# Sidebar Setup with Enhanced Styling
st.sidebar.markdown("""
<div style="
    background: #1a1a1a;
    border: 2px solid #D4AF37;
    padding: 1rem 0.8rem;
    border-radius: 12px;
    margin-bottom: 1rem;
    text-align: center;
    box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
">
    <h2 style="color: #ffffff; margin: 0; font-weight: 700; font-size: 1.5rem;">🌎 Travel Assistant</h2>
    <p style="color: #D4AF37; margin: 0.3rem 0 0 0; font-weight: 500; font-size: 0.9rem;">Personalize Your Journey</p>
</div>
""", unsafe_allow_html=True)

# Enhanced Travel Preferences with Cool Effects
st.sidebar.markdown("""
<div style="margin: 1rem 0;">
    <div style="
        background: #1a1a1a;
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
        transition: all 0.3s ease;
    ">
        <h4 style="color: #ffffff; text-align: center; margin-bottom: 0.5rem; font-weight: 600; font-size: 1.1rem;">💰 Budget Preference</h4>
        <div style="text-align: center; margin-top: 0.5rem;">
            <p style="color: #D4AF37; font-size: 0.8rem; font-style: italic; margin: 0;">Choose your comfort level</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Enhanced Budget Selection
budget = st.sidebar.radio(
    "Select Your Budget Range:",
    ["💸 Economy", "💳 Standard", "💎 Luxury"],
    label_visibility="collapsed"
)

st.sidebar.markdown("""
<div style="margin: 1rem 0;">
    <div style="
        background: #1a1a1a;
        border: 2px solid #D4AF37;
        border-radius: 12px;
        padding: 1rem;
        margin-bottom: 1rem;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.4);
        transition: all 0.3s ease;
    ">
        <h4 style="color: #ffffff; text-align: center; margin-bottom: 0.5rem; font-weight: 600; font-size: 1.1rem;">✈️ Flight Class</h4>
        <div style="text-align: center; margin-top: 0.5rem;">
            <p style="color: #D4AF37; font-size: 0.8rem; font-style: italic; margin: 0;">Your flying experience</p>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# Enhanced Flight Class Selection
flight_class = st.sidebar.radio(
    "Choose Your Flight Experience:",
    ["🪑 Economy", "💺 Business", "👑 First Class"],
    label_visibility="collapsed"
)

# Compact Travel Inspiration Box
st.sidebar.markdown("""
<div style="
    background: #1a1a1a;
    border: 2px solid #D4AF37;
    border-radius: 15px;
    padding: 1.5rem;
    margin-top: 1rem;
    text-align: center;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
">
    <h5 style="color: #ffffff; margin-bottom: 0.5rem; font-size: 1rem;">✨ Travel Inspiration</h5>
    <p style="color: #D4AF37; font-size: 0.8rem; line-height: 1.3; margin: 0;">
        "The world is a book and those who do not travel read only one page."
    </p>
    <p style="color: #ffffff; font-size: 0.7rem; margin: 0.5rem 0 0 0;">
        - Saint Augustine
    </p>
</div>
""", unsafe_allow_html=True)

# Convert city/country to IATA code for API params
source_iata = get_iata_code(source)
destination_iata = get_iata_code(destination)
params = {
    "engine": "google_flights",
    "departure_id": source_iata,
    "arrival_id": destination_iata,
    "outbound_date": str(departure_date),
    "return_date": str(return_date),
    "currency": "INR",
    "hl": "en",
    "api_key": config.SERPAPI_KEY
}

# Function to fetch flight data using Amadeus API
@st.cache_data(ttl=300)  # 5 minute cache for production
def fetch_amadeus_flights(source, destination, departure_date, return_date, adults=1):
    """Fetch flight offers using Amadeus Production API (api.amadeus.com)"""
    try:
        # Ensure IATA codes are valid 3-letter codes
        if len(source) != 3 or len(destination) != 3:
            st.warning(f"Invalid IATA codes: {source} -> {destination}")
            return []
            
        # Show that we're using production API
        st.info(f"🌐 **Searching Amadeus Production API** (api.amadeus.com) for {source} → {destination}")
        
        response = amadeus.shopping.flight_offers_search.get(
            originLocationCode=source,
            destinationLocationCode=destination,
            departureDate=str(departure_date),
            returnDate=str(return_date),
            adults=adults,
            currencyCode='ZAR',
            max=3
        )
        
        if response.data:
            st.success(f"✅ **Production API Response:** Found {len(response.data)} real flight offers from Amadeus")
        
        return response.data
    except ResponseError as error:
        st.error(f"Amadeus Flight API Error: {error}")
        st.info("Using fallback data - some features may be limited")
        return generate_mock_flight_data(source, destination, departure_date, return_date, adults)
    except Exception as e:
        st.error(f"Flight search error: {str(e)}")
        return generate_mock_flight_data(source, destination, departure_date, return_date, adults)

def generate_mock_flight_data(source, destination, departure_date, return_date, adults=1):
    """Generate realistic mock flight data for development"""
    import random
    from datetime import timedelta
    
    # Get city names for display
    city_names = {
        'JNB': 'Johannesburg', 'CPT': 'Cape Town', 'DUR': 'Durban',
        'LHR': 'London', 'JFK': 'New York', 'CDG': 'Paris',
        'LAX': 'Los Angeles', 'NRT': 'Tokyo', 'SYD': 'Sydney'
    }
    
    source_city = city_names.get(source, source)
    dest_city = city_names.get(destination, destination)
    
    # Generate 3-5 mock flights with realistic pricing
    base_prices = {
        ('JNB', 'CPT'): 1200, ('CPT', 'JNB'): 1200,
        ('JNB', 'DUR'): 800, ('DUR', 'JNB'): 800,
        ('CPT', 'DUR'): 1400, ('DUR', 'CPT'): 1400,
    }
    
    route_key = (source, destination)
    base_price = base_prices.get(route_key, 2500)  # Default for international
    
    airlines = ['South African Airways', 'FlySafair', 'Kulula', 'Lift', 'British Airways', 'Emirates']
    
    mock_flights = []
    for i in range(3):
        price_variation = random.uniform(0.8, 1.4)
        flight_price = round(base_price * price_variation * adults)
        
        # Generate realistic flight times
        departure_time = f"{random.randint(6, 22):02d}:{random.choice(['00', '15', '30', '45'])}"
        duration_hours = random.randint(1, 12)
        duration_mins = random.choice([0, 15, 30, 45])
        
        mock_flights.append({
            'price': {'total': str(flight_price), 'currency': 'ZAR'},
            'airline': random.choice(airlines),
            'departure_time': departure_time,
            'duration': f"{duration_hours}h {duration_mins}m",
            'source': source_city,
            'destination': dest_city,
            'stops': random.choice([0, 0, 0, 1]),  # Mostly direct flights
            'aircraft': random.choice(['Boeing 737', 'Airbus A320', 'Boeing 787']),
            'mock_data': True
        })
    
    return mock_flights

def generate_mock_restaurants(location, cuisine_type="", budget=""):
    """Generate realistic mock restaurant data for development"""
    import random
    
    # Sample restaurant data based on location
    restaurant_types = {
        'african': ['Shisa Nyama', 'Braai House', 'African Kitchen', 'Ubuntu Restaurant'],
        'italian': ['Mama Mia', 'Bella Vista', 'Romano\'s', 'La Piazza'],
        'asian': ['Dragon Palace', 'Sakura Sushi', 'Thai Garden', 'Panda Express'],
        'steakhouse': ['The Grill House', 'Prime Cuts', 'Steakhouse 101', 'Meat & Fire'],
        '': ['Local Favorite', 'City Bistro', 'Corner Cafe', 'Downtown Eatery']
    }
    
    cuisine_key = cuisine_type.lower() if cuisine_type else ''
    base_names = restaurant_types.get(cuisine_key, restaurant_types[''])
    
    price_ranges = {
        'budget': ('R50-150', 2),
        'mid-range': ('R150-300', 3),
        'luxury': ('R300-600', 4),
        '': ('R100-250', 3)
    }
    
    price_range, rating_base = price_ranges.get(budget.lower(), price_ranges[''])
    
    mock_restaurants = []
    for i in range(min(5, len(base_names))):
        name = f"{base_names[i]} - {location}"
        rating = round(rating_base + random.uniform(-0.5, 0.8), 1)
        rating = min(5.0, max(1.0, rating))  # Keep between 1-5
        
        mock_restaurants.append({
            'name': name,
            'rating': rating,
            'price_level': rating_base,
            'price_range': price_range,
            'cuisine_type': cuisine_type or 'Local',
            'vicinity': f"Near {location} center",
            'opening_hours': 'Open now' if random.choice([True, False]) else 'Opens at 18:00',
            'mock_data': True
        })
    
    return mock_restaurants

def parse_amadeus_flights(flight_data):
    """Parse Amadeus flight data to match your existing structure"""
    parsed_flights = []
    
    for offer in flight_data:
        price = offer['price']['total']
        currency = offer['price']['currency']
        
        # Get flight segments - safely check if itineraries exist
        if 'itineraries' not in offer or not offer['itineraries']:
            continue  # Skip this offer if no itineraries
            
        itineraries = offer['itineraries']
        if not itineraries[0].get('segments'):
            continue  # Skip if no segments
            
        outbound = itineraries[0]['segments'][0]
        return_flight = itineraries[1]['segments'][0] if len(itineraries) > 1 and itineraries[1].get('segments') else None
        
        # Calculate total duration - safely access duration
        total_duration = itineraries[0].get('duration', 'N/A')
        if return_flight and len(itineraries) > 1:
            return_duration = itineraries[1].get('duration', 'N/A')
            # Convert PT4H30M format to minutes
            total_duration = parse_duration(total_duration) + parse_duration(return_duration)
        else:
            total_duration = parse_duration(total_duration)
        
        flight_info = {
            'price': f"{currency} {price}",
            'total_duration': f"{total_duration} min",
            'airline': outbound.get('carrierCode', 'Unknown'),
            'airline_logo': f"https://pics.avs.io/100/100/{outbound.get('carrierCode', 'XX')}.png",
            'flights': [{
                'departure_airport': {
                    'code': outbound.get('departure', {}).get('iataCode', 'N/A'),
                    'time': outbound.get('departure', {}).get('at', 'N/A')
                },
                'arrival_airport': {
                    'code': outbound.get('arrival', {}).get('iataCode', 'N/A'),
                    'time': outbound.get('arrival', {}).get('at', 'N/A')
                }
            }],
            'booking_token': offer.get('id', 'N/A')  # Use offer ID for booking
        }
        
        parsed_flights.append(flight_info)
    
    return parsed_flights

def parse_duration(duration_str):
    """Convert PT4H30M format to total minutes"""
    import re
    pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?'
    match = re.match(pattern, duration_str)
    if match:
        hours = int(match.group(1) or 0)
        minutes = int(match.group(2) or 0)
        return hours * 60 + minutes
    return 0

# Function to extract top 3 cheapest flights
def extract_cheapest_flights(flight_data):
    """Extract and sort flights by price"""
    if not flight_data:
        return []
    
    # Sort by price (remove currency symbol for sorting)
    def get_price_value(flight):
        price_str = flight.get('price', '0')
        # Extract numeric value from "ZAR 1500" format
        try:
            return float(price_str.split(' ')[1])
        except:
            return float('inf')
    
    sorted_flights = sorted(flight_data, key=get_price_value)
    return sorted_flights[:3]  # Return top 3 cheapest

def get_airport_display_name(airport_code):
    """Get display name for airport"""
    location_names = {
        'JNB': 'Johannesburg (O.R. Tambo)',
        'CPT': 'Cape Town International',
        'DUR': 'Durban (King Shaka)',
        'NYC': 'New York (JFK/LGA/EWR)',
        'LAX': 'Los Angeles International',
        'LHR': 'London Heathrow',
        'CDG': 'Paris Charles de Gaulle',
        'NRT': 'Tokyo Narita',
        'SYD': 'Sydney Kingsford Smith'
    }
    return location_names.get(airport_code, f"{airport_code} Airport")

# Kiwi.com Cheap Flights API Integration (Primary flight source)
@st.cache_data(ttl=300)  # 5 minute cache
def fetch_kiwi_flights(source_iata, destination_iata, departure_date, return_date, departure_time_pref="Any Time", return_time_pref="Any Time", num_travelers=1):
    """Fetch flight data from Kiwi.com API with time preferences - Primary flight source"""
    try:
        import requests
        
        # Kiwi.com RapidAPI endpoint (correct endpoint found)
        url = "https://kiwi-com-cheap-flights.p.rapidapi.com/round-trip"
        
        headers = {
            "X-RapidAPI-Key": config.RAPIDAPI_KEY or "demo_key",
            "X-RapidAPI-Host": "kiwi-com-cheap-flights.p.rapidapi.com"
        }
        
        # Convert time preferences to hour ranges for Kiwi API
        time_ranges = {
            "🌅 Morning (06:00-12:00)": {"departure_times_from": "06:00", "departure_times_to": "12:00"},
            "☀️ Afternoon (12:00-18:00)": {"departure_times_from": "12:00", "departure_times_to": "18:00"}, 
            "🌙 Evening (18:00-00:00)": {"departure_times_from": "18:00", "departure_times_to": "23:59"},
            "🦉 Late Night (00:00-06:00)": {"departure_times_from": "00:00", "departure_times_to": "06:00"},
            "⏰ Any Time": {}
        }
        
        departure_time_filter = time_ranges.get(departure_time_pref, {})
        return_time_filter = time_ranges.get(return_time_pref, {})
        
        # Try multiple parameter formats for better compatibility
        parameter_sets = [
            # Format 1: Standard airport codes
            {
                "from": source_iata,
                "to": destination_iata,
                "departure": str(departure_date),
                "return": str(return_date),
                "adults": str(num_travelers),
                "currency": "USD",
                "limit": "10"
            },
            # Format 2: With country codes for South African routes
            {
                "fly_from": f"{source_iata}",
                "fly_to": f"{destination_iata}",
                "date_from": str(departure_date),
                "date_to": str(departure_date),
                "return_from": str(return_date),
                "return_to": str(return_date),
                "adults": num_travelers,
                "curr": "USD",
                "limit": 10
            },
            # Format 3: City-based search
            {
                "origin": source_iata,
                "destination": destination_iata,
                "departure_date": str(departure_date),
                "return_date": str(return_date),
                "passengers": str(num_travelers),
                "currency": "USD"
            }
        ]
        
        st.info(f"🌐 Searching Kiwi.com for flights from {source_iata} to {destination_iata}")
        
        # Try each parameter format
        for i, querystring in enumerate(parameter_sets, 1):
            try:
                st.info(f"🔄 Trying parameter format {i}/3...")
                response = requests.get(url, headers=headers, params=querystring, timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Parse Kiwi.com response - they use 'itineraries' not 'data'
                    flights = []
                    flight_data_array = data.get("itineraries", data.get("data", []))
                    
                    if len(flight_data_array) > 0:
                        st.success(f"✅ Found flights using parameter format {i}")
                        
                        for flight_data in flight_data_array[:5]:  # Get top 5 flights
                            
                            # Handle different Kiwi.com response formats
                            if "route" in flight_data:
                                # Format 1: Traditional Kiwi format
                                route = flight_data.get("route", [])
                                if not route:
                                    continue
                                
                                departure_flight = route[0]
                                departure_time = departure_flight.get("local_departure", "")[:16].replace("T", " ")
                                arrival_time = departure_flight.get("local_arrival", "")[:16].replace("T", " ")
                                airline = departure_flight.get("airline", "Various Airlines")
                                
                                duration_sec = flight_data.get("duration", {}).get("total", 0)
                                duration_hours = duration_sec // 3600
                                duration_mins = (duration_sec % 3600) // 60
                                duration = f"{duration_hours}h {duration_mins}m"
                                
                            else:
                                # Format 2: Alternative Kiwi format
                                departure_time = flight_data.get("departure_time", flight_data.get("departure", "N/A"))
                                arrival_time = flight_data.get("arrival_time", flight_data.get("arrival", "N/A"))
                                airline = flight_data.get("airline", flight_data.get("carrier", "Various Airlines"))
                                duration = flight_data.get("duration", "N/A")
                            
                            # Get price
                            price = flight_data.get("price", 0)
                            if isinstance(price, (int, float)):
                                price_str = f"${price:.0f}"
                            else:
                                price_str = str(price)
                            
                            # Generate Skyscanner booking URL with traveler count
                            skyscanner_url = f"https://www.skyscanner.com/transport/flights/{source_iata}/{destination_iata}/{departure_date}/{return_date}/?adults={num_travelers}&children=0&infants=0&cabinclass=economy"
                            
                            flight_info = {
                                "airline": airline,
                                "price": price_str,
                                "departure_time": departure_time,
                                "arrival_time": arrival_time,
                                "duration": duration,
                                "booking_url": skyscanner_url,  # Direct to Skyscanner
                                "stops": len(flight_data.get("route", [])) - 1 if "route" in flight_data else 0,
                                "source": "Kiwi.com → Skyscanner",
                                "flight_number": flight_data.get("flight_no", ""),
                                "aircraft": flight_data.get("vehicle_type", ""),
                                "booking_token": flight_data.get("booking_token", "")
                            }
                            flights.append(flight_info)
                        
                        if flights:
                            st.success(f"✈️ Found {len(flights)} flights from Kiwi.com")
                            return flights
                    else:
                        st.info(f"No flights found with parameter format {i}, trying next...")
                        continue
                        
                elif response.status_code == 429:
                    st.warning("⚠️ Rate limit reached for Kiwi.com API")
                    break
                else:
                    st.info(f"Format {i} returned status {response.status_code}, trying next...")
                    continue
                    
            except Exception as e:
                st.info(f"Format {i} failed: {str(e)[:50]}..., trying next...")
                continue
        
        # If no flights found with any format, try popular alternative routes
        st.warning("⚠️ No flights found with direct search. Checking alternative routes...")
        
        # For South African domestic routes, suggest alternatives
        if source_iata in ["DUR", "JNB", "CPT"] and destination_iata in ["DUR", "JNB", "CPT"]:
            st.info("💡 For South African domestic flights, trying major airlines...")
            return generate_south_african_domestic_flights(source_iata, destination_iata, departure_date, return_date)
        
        st.warning("⚠️ No flights found matching your criteria from Kiwi.com")
        return generate_enhanced_flight_mock_data(source_iata, destination_iata, departure_time_pref, return_time_pref)
            
    except Exception as e:
        st.info(f"Using demo flight data (Kiwi.com: {str(e)[:50]}...)")
        return generate_enhanced_flight_mock_data(source_iata, destination_iata, departure_time_pref, return_time_pref)

# Skyscanner API Integration for Enhanced Flight Search
@st.cache_data(ttl=300)  # 5 minute cache
def fetch_skyscanner_flights(source_iata, destination_iata, departure_date, return_date, departure_time_pref="Any Time", return_time_pref="Any Time"):
    """Fetch flight data from Skyscanner API with time preferences"""
    try:
        import requests
        
        # Skyscanner RapidAPI endpoint
        url = "https://skyscanner80.p.rapidapi.com/api/v1/flights/search-roundtrip"
        
        headers = {
            "X-RapidAPI-Key": config.RAPIDAPI_KEY or "demo_key",
            "X-RapidAPI-Host": "skyscanner80.p.rapidapi.com"
        }
        
        # Convert time preferences to hour ranges
        time_ranges = {
            "🌅 Morning (06:00-12:00)": ("06:00", "12:00"),
            "☀️ Afternoon (12:00-18:00)": ("12:00", "18:00"), 
            "🌙 Evening (18:00-00:00)": ("18:00", "00:00"),
            "🦉 Late Night (00:00-06:00)": ("00:00", "06:00"),
            "⏰ Any Time": (None, None)
        }
        
        departure_time_range = time_ranges.get(departure_time_pref, (None, None))
        return_time_range = time_ranges.get(return_time_pref, (None, None))
        
        querystring = {
            "fromId": source_iata,
            "toId": destination_iata,
            "departDate": str(departure_date),
            "returnDate": str(return_date),
            "adults": "1",
            "currency": "USD"
        }
        
        # Add time preferences if specified
        if departure_time_range[0]:
            querystring["departureTimeFrom"] = departure_time_range[0]
            querystring["departureTimeTo"] = departure_time_range[1]
        
        if return_time_range[0]:
            querystring["returnTimeFrom"] = return_time_range[0]
            querystring["returnTimeTo"] = return_time_range[1]
        
        response = requests.get(url, headers=headers, params=querystring, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            
            # Parse Skyscanner response
            flights = []
            if "data" in data and "itineraries" in data["data"]:
                for itinerary in data["data"]["itineraries"][:5]:  # Get top 5 flights
                    flight_info = {
                        "airline": itinerary.get("legs", [{}])[0].get("carriers", [{}])[0].get("name", "Unknown Airline"),
                        "price": f"${itinerary.get('price', {}).get('formatted', 'N/A')}",
                        "departure_time": itinerary.get("legs", [{}])[0].get("departure", "N/A"),
                        "arrival_time": itinerary.get("legs", [{}])[0].get("arrival", "N/A"),
                        "duration": f"{itinerary.get('legs', [{}])[0].get('durationInMinutes', 0) // 60}h {itinerary.get('legs', [{}])[0].get('durationInMinutes', 0) % 60}m",
                        "booking_url": f"https://www.skyscanner.com/transport/flights/{source_iata}/{destination_iata}/{departure_date}/{return_date}/",
                        "stops": len(itinerary.get("legs", [{}])[0].get("segments", [])) - 1,
                        "source": "Skyscanner API"
                    }
                    flights.append(flight_info)
            
            st.success(f"🛫 Found {len(flights)} Skyscanner flights with time preferences")
            return flights
            
        else:
            st.warning(f"Skyscanner API returned status {response.status_code}")
            return generate_enhanced_flight_mock_data(source_iata, destination_iata, departure_time_pref, return_time_pref)
            
    except Exception as e:
        st.info(f"Using demo flight data (Skyscanner: {str(e)[:50]}...)")
        return generate_enhanced_flight_mock_data(source_iata, destination_iata, departure_time_pref, return_time_pref)

def generate_south_african_domestic_flights(source_iata, destination_iata, departure_date, return_date):
    """Generate realistic South African domestic flight data"""
    
    # South African domestic airlines
    airlines = {
        "FlySafair": "https://www.flysafair.co.za/",
        "Kulula": "https://www.kulula.com/",
        "South African Airways": "https://www.flysaa.com/",
        "Lift": "https://www.lift.co.za/",
        "Airlink": "https://www.flyairlink.com/"
    }
    
    # Route-specific pricing (South African Rand converted to USD)
    route_pricing = {
        ("DUR", "JNB"): (85, 150),   # Durban to Johannesburg
        ("JNB", "DUR"): (85, 150),   # Johannesburg to Durban
        ("JNB", "CPT"): (95, 180),   # Johannesburg to Cape Town
        ("CPT", "JNB"): (95, 180),   # Cape Town to Johannesburg
        ("DUR", "CPT"): (120, 220),  # Durban to Cape Town
        ("CPT", "DUR"): (120, 220),  # Cape Town to Durban
    }
    
    route = (source_iata, destination_iata)
    base_price, max_price = route_pricing.get(route, (100, 200))
    
    flights = []
    for i, (airline, website) in enumerate(airlines.items()):
        price_variation = i * 15  # Price varies by airline
        price = base_price + price_variation
        
        # Time variations
        departure_times = ["06:30", "09:15", "12:45", "15:30", "18:20"]
        arrival_times = ["08:45", "11:30", "15:00", "17:45", "20:35"]
        
        flight = {
            "airline": airline,
            "price": f"${price}",
            "departure_time": departure_times[i % len(departure_times)],
            "arrival_time": arrival_times[i % len(arrival_times)],
            "duration": "1h 15m" if route[0] != route[1] else "1h 30m",
            "booking_url": website,
            "stops": 0,  # Domestic flights are usually direct
            "source": "South African Domestic (Demo)",
            "flight_number": f"{airline[:2].upper()}{100 + i}",
            "aircraft": "Boeing 737" if i % 2 == 0 else "Airbus A320",
            "booking_token": f"SA-{source_iata}{destination_iata}-{i}"
        }
        flights.append(flight)
    
    return flights

def generate_enhanced_flight_mock_data(source_iata, destination_iata, departure_time_pref="Any Time", return_time_pref="Any Time"):
    """Generate mock flight data with time preferences"""
    
    # Sample airlines
    airlines = ["Emirates", "Qatar Airways", "South African Airways", "British Airways", "Lufthansa"]
    
    # Time slots based on preferences
    time_slots = {
        "🌅 Morning (06:00-12:00)": ["07:30", "09:15", "11:45"],
        "☀️ Afternoon (12:00-18:00)": ["13:20", "15:30", "17:10"],
        "🌙 Evening (18:00-00:00)": ["19:45", "21:15", "23:30"],
        "🦉 Late Night (00:00-06:00)": ["01:20", "03:45", "05:15"],
        "⏰ Any Time": ["07:30", "13:20", "19:45"]
    }
    
    departure_times = time_slots.get(departure_time_pref, time_slots["⏰ Any Time"])
    
    flights = []
    for i, airline in enumerate(airlines[:3]):
        flight = {
            "airline": airline,
            "price": f"${850 + (i * 120)}",
            "departure_time": departure_times[i % len(departure_times)],
            "arrival_time": "14:20",  # Sample arrival
            "duration": f"{8 + i}h {30 + (i * 15)}m",
            "booking_url": f"https://www.skyscanner.com/transport/flights/{source_iata}/{destination_iata}/",
            "stops": i,  # 0, 1, 2 stops
            "source": "Demo Data (Time-filtered)"
        }
        flights.append(flight)
    
    return flights

# Google Search Functions for restaurants, attractions, and local activities
def fetch_google_restaurants(location, cuisine_type="", budget="", travel_theme=""):
    """Fetch restaurant recommendations using Google Places API with business-friendly options"""
    
    # Use Google Places API when available, fallback to mock data
    if not should_use_google_places():
        st.info("Google Places API not configured. Using sample restaurant data.")
        return generate_mock_restaurants(location, cuisine_type, budget)
    
    try:
        # First, get the location coordinates
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            st.warning(f"Could not find coordinates for {location}")
            return generate_mock_restaurants(location, cuisine_type, budget)
        
        location_coords = geocode_result[0]['geometry']['location']
        lat, lng = location_coords['lat'], location_coords['lng']
        
        # Search for restaurants using Places API with business-friendly options
        search_query = "restaurant"
        if cuisine_type:
            search_query += f" {cuisine_type}"
        
        # Add business-friendly terms for business travel theme
        if "Business" in travel_theme:
            search_query += " business lunch meeting wifi private dining"
        
        # Use nearby search for better results
        places_result = gmaps.places_nearby(
            location=(lat, lng),
            radius=10000,  # 10km radius
            type='restaurant',
            keyword=search_query,
            min_price=get_price_level(budget)
        )
        
        restaurants = []
        
        # Get detailed information for each restaurant
        for place in places_result.get('results', [])[:3]:  # Limit to 3 restaurants
            place_id = place['place_id']
            
            # Get detailed place information
            place_details = gmaps.place(
                place_id=place_id,
                fields=['name', 'formatted_address', 'formatted_phone_number', 
                       'website', 'rating', 'user_ratings_total', 'opening_hours',
                       'price_level', 'url']
            )
            
            details = place_details['result']
            
            # Format opening hours
            opening_hours = "Hours not available"
            if details.get('opening_hours') and details['opening_hours'].get('weekday_text'):
                opening_hours = "; ".join(details['opening_hours']['weekday_text'][:2])  # Show first 2 days
                if len(details['opening_hours']['weekday_text']) > 2:
                    opening_hours += "..."
            
            restaurant = {
                'name': details.get('name', 'Unknown Restaurant'),
                'address': details.get('formatted_address', 'Address not available'),
                'phone': details.get('formatted_phone_number', 'Phone not available'),
                'website': details.get('website', details.get('url', '')),
                'rating': details.get('rating', 'N/A'),
                'total_ratings': details.get('user_ratings_total', 0),
                'price_level': get_price_text(details.get('price_level')),
                'hours': opening_hours,
                'photo_url': '',  # Simplified for now
                'review_snippet': 'Visit Google Maps for reviews',  # Simplified
                'google_maps_url': details.get('url', ''),
                'place_id': place_id,
                'source': 'Google Places API'
            }
            restaurants.append(restaurant)
        
        return restaurants
        
    except Exception as error:
        st.error(f"Google Places Restaurant Search Error: {error}")
        return []

def fetch_business_venues(location):
    """Fetch business-friendly venues like coworking spaces, conference centers, meeting rooms"""
    
    if not should_use_google_places():
        st.info("Google Places API not configured. Using sample business venue data.")
        return generate_mock_business_venues(location)
    
    try:
        # First, get the location coordinates
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            st.warning(f"Could not find coordinates for {location}")
            return generate_mock_business_venues(location)

        location_coords = geocode_result[0]['geometry']['location']
        lat, lng = location_coords['lat'], location_coords['lng']

        # Search for business venues
        business_types = [
            {'type': 'establishment', 'keyword': 'coworking space shared office', 'category': '💼 Coworking Space'},
            {'type': 'establishment', 'keyword': 'conference center meeting room', 'category': '🏢 Conference Center'},
            {'type': 'establishment', 'keyword': 'business center office space', 'category': '🏢 Business Center'},
            {'type': 'establishment', 'keyword': 'hotel business center meeting', 'category': '🏨 Hotel Business Center'}
        ]
        
        all_venues = []

        for venue_type in business_types:
            places_result = gmaps.places_nearby(
                location=(lat, lng),
                radius=15000,  # 15km radius
                keyword=venue_type['keyword']
            )

            for place in places_result.get('results', [])[:2]:  # 2 per type
                place_id = place['place_id']

                # Get detailed place information
                place_details = gmaps.place(
                    place_id=place_id,
                    fields=['name', 'formatted_address', 'formatted_phone_number',
                           'website', 'rating', 'user_ratings_total', 'opening_hours', 'url']
                )

                details = place_details['result']

                # Format opening hours
                opening_hours = "Hours not available"
                if details.get('opening_hours') and details['opening_hours'].get('weekday_text'):
                    opening_hours = "; ".join(details['opening_hours']['weekday_text'][:2])
                    if len(details['opening_hours']['weekday_text']) > 2:
                        opening_hours += "..."

                venue = {
                    'name': details.get('name', 'Unknown Venue'),
                    'address': details.get('formatted_address', 'Address not available'),
                    'phone': details.get('formatted_phone_number', 'Phone not available'),
                    'website': details.get('website', ''),
                    'rating': details.get('rating', 'N/A'),
                    'total_ratings': details.get('user_ratings_total', 0),
                    'hours': opening_hours,
                    'category': venue_type['category'],
                    'google_maps_url': details.get('url', ''),
                    'place_id': place_id,
                    'source': 'Google Places API'
                }
                all_venues.append(venue)

        # Remove duplicates and limit to best venues
        unique_venues = {venue['place_id']: venue for venue in all_venues}.values()
        sorted_venues = sorted(unique_venues, key=lambda x: (x['rating'] if x['rating'] != 'N/A' else 0), reverse=True)

        return list(sorted_venues)[:4]  # Return top 4 business venues

    except Exception as error:
        st.error(f"Google Places Business Venues Search Error: {error}")
        return generate_mock_business_venues(location)

def generate_mock_business_venues(location):
    """Generate mock business venue data when API is unavailable"""
    return [
        {
            'name': f'{location} Business Center',
            'address': f'Central Business District, {location}',
            'phone': '+27 11 123 4567',
            'website': 'https://businesscenter.com',
            'rating': 4.2,
            'total_ratings': 156,
            'hours': 'Mon-Fri: 8:00 AM - 6:00 PM',
            'category': '🏢 Business Center',
            'google_maps_url': 'https://maps.google.com',
            'source': 'Demo Data'
        },
        {
            'name': f'{location} Coworking Hub',
            'address': f'Downtown {location}',
            'phone': '+27 11 234 5678',
            'website': 'https://coworkinghub.com',
            'rating': 4.5,
            'total_ratings': 89,
            'hours': 'Mon-Sun: 24/7 Access',
            'category': '💼 Coworking Space',
            'google_maps_url': 'https://maps.google.com',
            'source': 'Demo Data'
        }
    ]

# Helper functions for Google Places API
def get_price_level(budget):
    """Convert budget preference to Google Places price level"""
    # Extract the budget type from the enhanced format
    if "Economy" in budget:
        return 1
    elif "Standard" in budget:
        return 2
    elif "Luxury" in budget:
        return 3
    else:
        return 1  # Default to economy

def get_price_text(price_level):
    """Convert price level number to text"""
    if price_level is None:
        return "Price not available"
    
    price_text = {
        1: "$ (Inexpensive)",
        2: "$$ (Moderate)",
        3: "$$$ (Expensive)",
        4: "$$$$ (Very Expensive)"
    }
    return price_text.get(price_level, "Price not available")

def get_attraction_category(types):
    """Determine attraction category from Google Places types"""
    if 'museum' in types:
        return '🏛️ Museum'
    elif 'amusement_park' in types:
        return '🎢 Amusement Park'
    elif 'zoo' in types:
        return '🦁 Zoo'
    elif 'aquarium' in types:
        return '🐠 Aquarium'
    elif 'park' in types:
        return '🌳 Park'
    elif 'tourist_attraction' in types:
        return '🎯 Tourist Attraction'
    else:
        return '📍 Point of Interest'

def fetch_google_attractions(location, activity_preferences=""):
    """Fetch tourist attractions using Google Places API"""
    try:
        # Get location coordinates
        geocode_result = gmaps.geocode(location)
        if not geocode_result:
            st.warning(f"Could not find coordinates for {location}")
            return []
        
        location_coords = geocode_result[0]['geometry']['location']
        lat, lng = location_coords['lat'], location_coords['lng']
        
        # Search for different types of attractions
        attraction_types = ['tourist_attraction', 'museum', 'amusement_park', 'zoo', 'aquarium']
        all_attractions = []
        
        for attraction_type in attraction_types:
            search_query = attraction_type.replace('_', ' ')
            if activity_preferences:
                search_query += f" {activity_preferences}"
            
            places_result = gmaps.places_nearby(
                location=(lat, lng),
                radius=15000,  # 15km radius for attractions
                type=attraction_type,
                keyword=search_query
            )
            
            for place in places_result.get('results', [])[:2]:  # 2 per type
                place_id = place['place_id']
                
                # Get detailed place information
                place_details = gmaps.place(
                    place_id=place_id,
                    fields=['name', 'formatted_address', 'formatted_phone_number', 
                           'website', 'rating', 'user_ratings_total', 'opening_hours', 'url']
                )
                
                details = place_details['result']
                
                # Format opening hours
                opening_hours = "Hours not available"
                if details.get('opening_hours') and details['opening_hours'].get('weekday_text'):
                    opening_hours = "; ".join(details['opening_hours']['weekday_text'][:2])
                    if len(details['opening_hours']['weekday_text']) > 2:
                        opening_hours += "..."
                
                # Determine attraction category from place types
                place_types = place.get('types', [])
                category = get_attraction_category(place_types)
                
                attraction = {
                    'name': details.get('name', 'Unknown Attraction'),
                    'address': details.get('formatted_address', 'Address not available'),
                    'phone': details.get('formatted_phone_number', 'Phone not available'),
                    'website': details.get('website', ''),
                    'rating': details.get('rating', 'N/A'),
                    'total_ratings': details.get('user_ratings_total', 0),
                    'hours': opening_hours,
                    'photo_url': '',  # Simplified for now
                    'review_snippet': 'Visit Google Maps for reviews',  # Simplified
                    'google_maps_url': details.get('url', ''),
                    'category': category,
                    'place_types': place_types,
                    'place_id': place_id,
                    'source': 'Google Places API'
                }
                all_attractions.append(attraction)
        
        # Remove duplicates and limit to 3 best attractions
        unique_attractions = {attr['place_id']: attr for attr in all_attractions}.values()
        sorted_attractions = sorted(unique_attractions, key=lambda x: (x['rating'] if x['rating'] != 'N/A' else 0), reverse=True)
        
        return list(sorted_attractions)[:3]
        
    except Exception as error:
        st.error(f"Google Places Attractions Search Error: {error}")
        return []

def fetch_google_local_info(location):
    """Fetch local information with summaries and website links"""
    try:
        queries = [
            {
                'query': f"weather in {location} best time to visit climate",
                'category': 'Weather & Best Time to Visit',
                'icon': '🌤️'
            },
            {
                'query': f"local culture customs traditions {location}",
                'category': 'Local Culture & Customs',
                'icon': '🏛️'
            },
            {
                'query': f"safety tips travel advice {location}",
                'category': 'Safety & Travel Tips',
                'icon': '🛡️'
            },
            {
                'query': f"transportation getting around {location} public transport",
                'category': 'Transportation & Getting Around',
                'icon': '🚌'
            }
        ]
        
        all_info = []
        
        for query_info in queries:
            params = {
                "engine": "google",
                "q": query_info['query'],
                "location": location,
                "hl": "en",
                "gl": "za",
                "api_key": config.SERPAPI_KEY
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Get top 2 results for better summary
            if results.get("organic_results"):
                organic_results = results["organic_results"][:2]
                
                # Create a summary from multiple sources
                descriptions = []
                sources = []
                
                for result in organic_results:
                    snippet = result.get('snippet', '')
                    if snippet:
                        descriptions.append(snippet[:150] + "..." if len(snippet) > 150 else snippet)
                        sources.append({
                            'title': result.get('title', 'Source'),
                            'link': result.get('link', '')
                        })
                
                # Combine descriptions into a brief summary
                summary = " | ".join(descriptions)
                
                info = {
                    'category': query_info['category'],
                    'icon': query_info['icon'],
                    'summary': summary,
                    'sources': sources,
                    'full_description': ' '.join([result.get('snippet', '') for result in organic_results])
                }
                all_info.append(info)
        
        return all_info
    except Exception as error:
        st.error(f"Google Local Info Search Error: {error}")
        return []

def extract_rating_from_snippet(snippet):
    """Extract rating from Google search snippet"""
    try:
        if not snippet or not isinstance(snippet, str):
            return "N/A"
            
        import re
        # Look for patterns like "4.5 stars", "4.5/5", "Rating: 4.5"
        patterns = [
            r'(\d+\.?\d*)\s*(?:stars?|/5|\⭐)',
            r'(?:Rating|Rated):\s*(\d+\.?\d*)',
            r'(\d+\.?\d*)\s*out\s*of\s*5'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, snippet, re.IGNORECASE)
            if match:
                return f"{match.group(1)} ⭐"
        
        return "N/A"
    except Exception as e:
        return "N/A"

def fetch_live_events(location, departure_date, return_date):
    """Fetch live events and happenings during travel dates"""
    try:
        # Format dates for search queries
        from datetime import datetime
        if isinstance(departure_date, str):
            dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
        else:
            dep_date = departure_date
            
        if isinstance(return_date, str):
            ret_date = datetime.strptime(return_date, "%Y-%m-%d")
        else:
            ret_date = return_date
        
        # Create date range for search
        month_year = dep_date.strftime("%B %Y")
        
        event_queries = [
            {
                'query': f"events {location} {month_year} concerts shows festivals",
                'category': 'Concerts & Shows',
                'icon': '🎵'
            },
            {
                'query': f"festivals {location} {month_year} food music cultural",
                'category': 'Festivals & Cultural Events',
                'icon': '🎭'
            },
            {
                'query': f"sports events {location} {month_year} games matches tournaments",
                'category': 'Sports & Games',
                'icon': '⚽'
            },
            {
                'query': f"exhibitions museums {location} {month_year} art shows galleries",
                'category': 'Exhibitions & Museums',
                'icon': '🎨'
            },
            {
                'query': f"nightlife events {location} {month_year} clubs bars entertainment",
                'category': 'Nightlife & Entertainment',
                'icon': '🌃'
            }
        ]
        
        all_events = []
        
        for event_info in event_queries:
            params = {
                "engine": "google",
                "q": event_info['query'],
                "location": location,
                "hl": "en",
                "gl": "za",
                "api_key": config.SERPAPI_KEY
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            # Get events from organic results
            events_found = []
            organic_results = results.get("organic_results", [])
            
            for result in organic_results[:3]:  # Limit to 3 events per category
                title = result.get('title', 'Unknown Event')
                snippet = result.get('snippet', '')
                link = result.get('link', '')
                
                # Filter out general tourism sites, prefer specific event listings
                if any(keyword in title.lower() or keyword in snippet.lower() for keyword in 
                       ['event', 'concert', 'show', 'festival', 'exhibition', 'match', 'game', 'performance']):
                    
                    # Extract date information from snippet if available
                    import re
                    date_patterns = [
                        r'(\d{1,2}[-/]\d{1,2}[-/]\d{4})',
                        r'(\d{1,2}\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{4})',
                        r'((Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\s+\d{1,2}[-,]?\s*\d{4})'
                    ]
                    
                    event_date = "Date TBA"
                    for pattern in date_patterns:
                        match = re.search(pattern, snippet, re.IGNORECASE)
                        if match:
                            event_date = match.group(1)
                            break
                    
                    # Determine if it's a booking or info site
                    if any(keyword in link.lower() for keyword in ['tickets', 'booking', 'eventbrite', 'ticketek', 'quicket']):
                        link_type = "🎫 **Ticket Booking Site** - Purchase tickets directly"
                        link_text = "Buy Tickets"
                    elif any(keyword in link.lower() for keyword in ['facebook', 'instagram', 'twitter']):
                        link_type = "📱 **Social Media Event** - Follow for updates"
                        link_text = "View Event Details"
                    else:
                        link_type = "ℹ️ **Event Information** - Details and possibly booking"
                        link_text = "Learn More"
                    
                    event = {
                        'name': title,
                        'description': snippet[:200] + "..." if len(snippet) > 200 else snippet,
                        'date': event_date,
                        'website': link,
                        'link_type': link_type,
                        'link_text': link_text,
                        'category': event_info['category'],
                        'icon': event_info['icon']
                    }
                    events_found.append(event)
            
            if events_found:
                all_events.extend(events_found)
        
        return all_events[:12]  # Return top 12 events across all categories
        
    except Exception as error:
        st.error(f"Live Events Search Error: {error}")
        return []

# AI Agents
researcher = Agent(
    name="Researcher",
    instructions=[
        "Identify the travel destination specified by the user.",
        "Gather detailed information on the destination, including climate, culture, and safety tips.",
        "Find popular attractions, landmarks, and must-visit places.",
        "Search for activities that match the user’s interests and travel style.",
        "Prioritize information from reliable sources and official travel guides.",
        "Provide well-structured summaries with key insights and recommendations."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

planner = Agent(
    name="Planner",
    instructions=[
        "Gather details about the user's travel preferences and budget.",
        "Create a detailed itinerary with scheduled activities and estimated costs.",
        "Ensure the itinerary includes transportation options and travel time estimates.",
        "Optimize the schedule for convenience and enjoyment.",
        "Present the itinerary in a structured format."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

hotel_restaurant_finder = Agent(
    name="Hotel & Restaurant Finder",
    instructions=[
        "Identify key locations in the user's travel itinerary.",
        "Search for highly rated hotels near those locations.",
        "Search for top-rated restaurants based on cuisine preferences and proximity.",
        "Prioritize results based on user preferences, ratings, and availability.",
        "Provide direct booking links or reservation options where possible."
    ],
    model=Gemini(id="gemini-2.0-flash-exp"),
    add_datetime_to_instructions=True,
)

# Generate Travel Plan with persistent display
if st.button("🚀 Generate Travel Plan") or st.session_state.plan_generated:
    
    # Only run the generation process if not already generated
    if not st.session_state.plan_generated:
        st.session_state.plan_generated = True
        
        # Add a "Generate New Plan" button at the top when plan is shown
        if st.button("🔄 Generate New Plan", key="new_plan_btn"):
            st.session_state.plan_generated = False
            st.rerun()
    
    else:
        # Show the "Generate New Plan" button when plan is displayed
        col1, col2 = st.columns([1, 4])
        with col1:
            if st.button("🔄 Generate New Plan", key="new_plan_btn_displayed"):
                st.session_state.plan_generated = False
                st.rerun()
    with st.spinner("✈️ Searching flight options..."):
        # Use Kiwi.com as primary flight source for pricing data
        st.info(f"🕐 Searching flights with preferences: Departure {departure_time_pref}, Return {return_time_pref}")
        
        all_flights = []
        
        # Primary search: Kiwi.com (provides good pricing data)
        kiwi_flights = fetch_kiwi_flights(source_iata, destination_iata, departure_date, return_date, departure_time_pref, return_time_pref, num_travelers)
        if kiwi_flights:
            all_flights.extend(kiwi_flights)
            st.success(f"✅ Found {len(kiwi_flights)} flight options")
        else:
            st.info("ℹ️ No direct flights found, but Skyscanner will show all available options")
        
        # Note: All booking redirects to Skyscanner for actual purchases

    # Car rental search using streamlined approach (no API needed)
    st.info("🚗 Car rental options available via Skyscanner")
    car_rental_data = []  # No API data needed - direct to Skyscanner

    with st.spinner("🍽️ Finding best restaurants with Google..."):
        # Use Google for restaurants (better local business data)
        restaurant_data = fetch_google_restaurants(destination, budget=budget, travel_theme=travel_theme)

    # Add business venues search for business trips
    business_venues = []
    if "Business" in travel_theme:
        with st.spinner("💼 Finding business venues and coworking spaces..."):
            business_venues = fetch_business_venues(destination)

    with st.spinner("🎯 Discovering attractions with Google..."):
        # Use Google for tourist attractions (comprehensive local info)
        attraction_data = fetch_google_attractions(destination, activity_preferences)

    with st.spinner("🎉 Finding live events during your trip..."):
        # Fetch live events happening during travel dates
        live_events = fetch_live_events(destination, departure_date, return_date)

    with st.spinner("ℹ️ Gathering local information with Google..."):
        # Use Google for local culture, weather, safety info
        local_info = fetch_google_local_info(destination)

    # AI Processing with combined data
    # Calculate trip duration from dates
    trip_duration = (return_date - departure_date).days
    if trip_duration <= 0:
        trip_duration = 1  # Minimum 1 day trip

    with st.spinner("🔍 Creating comprehensive travel insights..."):
        # Combine all data for AI processing
        combined_travel_data = {
            'restaurants': restaurant_data,
            'attractions': attraction_data,
            'local_info': local_info,
            'live_events': live_events
        }
        
        research_prompt = (
            f"Based on real-time data for {destination}, provide comprehensive travel insights:\n"
            f"- Popular Attractions: {', '.join([a.get('name', 'Attraction') for a in attraction_data[:5]]) if attraction_data else 'Research local attractions'}\n"
            f"- Upcoming Events: {', '.join([e.get('title', 'Event') for e in live_events[:3]]) if live_events else 'Check local event listings'}\n"
            f"- Local Highlights: {', '.join([info.get('category', 'Local info') for info in local_info[:3]]) if local_info else 'General destination information'}\n"
            f"Create a detailed guide covering:\n"
            f"1. Must-visit attractions and activities for a {travel_theme.lower()} trip\n"
            f"2. Live events and happenings during travel dates\n"
            f"3. Local culture and customs\n"
            f"4. Weather and best time to visit\n"
            f"5. Safety tips and transportation\n"
            f"6. Recommendations based on traveler preferences: {activity_preferences}\n"
            f"Trip duration: {trip_duration} days, Budget: {budget}, Flight Class: {flight_class}\n"
            f"Focus on providing practical, actionable travel advice without technical data."
        )
        research_results = researcher.run(research_prompt, stream=False)

    with st.spinner("🗺️ Creating your personalized itinerary..."):
        # Create a clean summary for the AI instead of raw JSON
        if all_flights:
            try:
                first_flight = all_flights[0]
                price = first_flight.get('price', 'N/A')
                airline = first_flight.get('airline', 'Various Airlines')
                flight_summary = f"Available flights from {source_iata} to {destination_iata}, starting from {price} with {airline}"
            except (KeyError, IndexError):
                flight_summary = f"Flight options available with {len(all_flights)} choices"
        else:
            flight_summary = "Flight search results will be available via Skyscanner"
        
        car_rental_summary = "Car rental options available via Skyscanner"
        
        restaurant_summary = f"Featured restaurants include {', '.join([r.get('name', 'Restaurant') for r in restaurant_data[:3]]) if restaurant_data else 'local dining options'}"
        
        attraction_summary = f"Top attractions include {', '.join([a.get('name', 'Attraction') for a in attraction_data[:3]]) if attraction_data else 'local points of interest'}"
        
        events_summary = f"Live events during your visit: {', '.join([e.get('title', 'Various events') for e in live_events[:3]]) if live_events else 'Check local listings'}"
        
        planning_prompt = (
            f"Create a detailed {trip_duration}-day itinerary for a {travel_theme.lower()} trip to {destination}. "
            f"Use this information to create recommendations:\n\n"
            f"AVAILABLE SERVICES:\n"
            f"- Flights: {flight_summary}\n"
            f"- Transportation: {car_rental_summary}\n"
            f"- Dining: {restaurant_summary}\n"
            f"- Attractions: {attraction_summary}\n"
            f"- Events: {events_summary}\n\n"
            f"TRAVELER PREFERENCES:\n"
            f"- Activities: {activity_preferences}\n"
            f"- Budget: {budget}\n"
            f"- Flight Class: {flight_class}\n"
            f"- Departure Time Preference: {departure_time_pref}\n"
            f"- Return Time Preference: {return_time_pref}\n\n"
            f"- Flight Class: {flight_class}\n\n"
            f"RESEARCH INSIGHTS:\n{research_results.content}\n\n"
            f"CRITICAL FORMATTING INSTRUCTIONS:\n"
            f"- Use ONLY plain text and basic markdown formatting\n"
            f"- NO HTML tags whatsoever (no <div>, <span>, <style>, etc.)\n"
            f"- NO CSS styling or HTML formatting\n"
            f"- Use simple markdown: # for headers, ** for bold, - for bullets\n"
            f"- Create clear, readable text that displays properly in a travel app\n"
            f"- Focus on practical travel information with specific times and locations\n\n"
            f"Create a detailed day-by-day itinerary including recommended restaurants, attractions, and events from the available data."
        )
        itinerary = planner.run(planning_prompt, stream=False)

    # Display Results
    st.subheader("✈️ Flight Booking")
    st.info(f"🕐 Preferred departure: {departure_time_pref} | Return: {return_time_pref}")
    
    if all_flights:
        # Get price range from available flights
        try:
            def get_price_numeric(flight):
                price_str = flight.get("price", "$999")
                return float(price_str.replace("$", "").replace(",", ""))
            
            prices = [get_price_numeric(flight) for flight in all_flights]
            min_price = min(prices)
            max_price = max(prices)
            
            if min_price == max_price:
                price_range = f"from ${min_price:.0f}"
            else:
                price_range = f"${min_price:.0f} - ${max_price:.0f}"
        except:
            price_range = "Various prices available"
        
        # Generate Skyscanner URL for direct booking with traveler count
        skyscanner_url = f"https://www.skyscanner.com/transport/flights/{source_iata}/{destination_iata}/{departure_date.strftime('%y%m%d')}/{return_date.strftime('%y%m%d')}/?adults={num_travelers}&children=0&infants=0&cabinclass=economy"
        
        st.success(f"✅ Found {len(all_flights)} flight options available")
        
        # Show traveler info in display
        travelers_text = "1 traveler" if num_travelers == 1 else f"{num_travelers} travelers"
        
        st.markdown(f"""
        ### 🎯 Ready to Book Your Flight?
        
        **📍 Route:** {source_iata} ➜ {destination_iata} ➜ {source_iata}  
        **📅 Dates:** {departure_date.strftime('%b %d')} - {return_date.strftime('%b %d, %Y')}  
        **👥 Travelers:** {travelers_text}  
        **💰 Price Range:** {price_range}  
        **✈️ Airlines:** Multiple carriers available  
        
        ---
        
        ### 🌟 **[View & Book All Flight Options on Skyscanner]({skyscanner_url})**
        
        *Click the link above to see all available flights for your dates and book directly with your preferred airline.*
        """)
    else:
        st.warning("⚠️ No flight data available. Please try different dates or destinations.")
        
        # Still provide Skyscanner link even if no flights found
        travelers_text = "1 traveler" if num_travelers == 1 else f"{num_travelers} travelers"
        skyscanner_url = f"https://www.skyscanner.com/transport/flights/{source_iata}/{destination_iata}/{departure_date.strftime('%y%m%d')}/{return_date.strftime('%y%m%d')}/?adults={num_travelers}&children=0&infants=0&cabinclass=economy"
        st.markdown(f"""
        ### 📍 Search Manually on Skyscanner
        **[🔍 Search flights for {source_iata} to {destination_iata} ({travelers_text})]({skyscanner_url})**
        """)

    # Car Rental Booking Section
    st.subheader("🚗 Car Rental Booking")
    
    # Generate Skyscanner car rental URL using correct format
    pickup_date_str = departure_date.strftime('%Y-%m-%dT10:00')
    dropoff_date_str = return_date.strftime('%Y-%m-%dT10:00')
    
    # Use actual Skyscanner car hire URL structure
    # Note: Using generic location ID format - Skyscanner will redirect properly
    skyscanner_car_url = f"https://www.skyscanner.com/carhire/results/{destination_iata}/{destination_iata}/{pickup_date_str}/{dropoff_date_str}/30/"
    
    # Get rental duration
    rental_days = (return_date - departure_date).days
    rental_duration = f"{rental_days} day{'s' if rental_days != 1 else ''}"
    
    st.markdown(f"""
    ### 🎯 Ready to Book Your Car Rental?
    
    **📍 Pickup Location:** {get_airport_display_name(destination_iata)}  
    **📅 Rental Period:** {departure_date.strftime('%b %d')} - {return_date.strftime('%b %d, %Y')} ({rental_duration})  
    **� Travelers:** {num_travelers}  
    **💰 Budget:** {budget} (prices shown in South African Rand)  
    
    ---
    
    ### 🌟 **[Find & Book Your Car Rental on Skyscanner]({skyscanner_car_url})**
    
    *Click the link above to compare all available rental cars and book directly with your preferred provider.*
    """)

    # Display specific restaurant recommendations with direct links
    st.markdown('<div class="section-header">🍽️ Restaurant Recommendations</div>', unsafe_allow_html=True)
    if restaurant_data:
        st.markdown("**Professional restaurant recommendations with verified business details:**")
        
        # Show all restaurants in an expandable dropdown
        with st.expander(f"🍽️ View All {len(restaurant_data)} Restaurant Recommendations"):
            for idx, restaurant in enumerate(restaurant_data, 1):
                restaurant_name = restaurant['name']
                address = restaurant.get('address', 'Address not available')
                phone = restaurant.get('phone', 'Phone not available')
                website = restaurant.get('website', '#')
                rating = restaurant.get('rating', 'N/A')
                total_ratings = restaurant.get('total_ratings', 0)
                price_level = restaurant.get('price_level', 'Price not available')
                hours = restaurant.get('hours', 'Hours not available')
                review_snippet = restaurant.get('review_snippet', 'No reviews available')
                google_maps_url = restaurant.get('google_maps_url', '#')
                photo_url = restaurant.get('photo_url', '')
                source = restaurant.get('source', 'Google Places API')
                
                # Determine the type of link and booking capability
                if 'Website' in source:
                    link_type = "🍴 **Direct Restaurant Website** - Book tables, view menu, contact directly"
                    link_text = "Visit Restaurant Website"
                else:
                    link_type = "� **Google Maps Location** - View location, reviews, and contact info"
                    link_text = "View on Google Maps"
                
                st.markdown(f"""
                ### {idx}. 🍽️ {restaurant_name}
                
                **⭐ Rating:** {rating}/5 ({total_ratings} reviews)  
                **📍 Address:** {address}  
                **📞 Phone:** {phone}  
                **🕒 Hours:** {hours}  
                **� Price Level:** {price_level}  
                
                **🔗 Link Type:** {link_type}  
                **� Source:** {source}
                
                **[{link_text}]({website})**
                """)
                st.markdown("---")
    else:
        st.info("🍽️ Restaurant search powered by Google Places API")

    # Display business venues for business trips
    if "Business" in travel_theme and business_venues:
        st.subheader("💼 Business Venues & Coworking Spaces")
        st.markdown("**Professional business venues perfect for meetings and work:**")
        
        with st.expander(f"💼 View All {len(business_venues)} Business Venues"):
            for idx, venue in enumerate(business_venues, 1):
                venue_name = venue['name']
                address = venue.get('address', 'Address not available')
                phone = venue.get('phone', 'Phone not available')
                website = venue.get('website', '#')
                rating = venue.get('rating', 'N/A')
                total_ratings = venue.get('total_ratings', 0)
                hours = venue.get('hours', 'Hours not available')
                category = venue.get('category', '💼 Business Venue')
                google_maps_url = venue.get('google_maps_url', '#')
                source = venue.get('source', 'Google Places API')
                
                st.markdown(f"""
                ### {idx}. {category} {venue_name}
                
                **⭐ Rating:** {rating}/5 ({total_ratings} reviews)  
                **📍 Address:** {address}  
                **📞 Phone:** {phone}  
                **🕒 Hours:** {hours}  
                
                **💼 Perfect for:** Business meetings, remote work, networking events
                
                **🔗 Links:**  
                • **[Visit Website]({website})** - Information, booking, amenities  
                • **[View on Google Maps]({google_maps_url})** - Directions, photos, reviews
                
                **📊 Source:** {source}
                """)
                
                if idx < len(business_venues):
                    st.markdown("---")
        st.info("💼 Business venues powered by Google Places API")

    # Display Google-sourced attractions with direct booking links
    st.subheader("🎯 Top Attractions & Activities")
    if attraction_data:
        st.markdown("**Verified tourist attractions with official information:**")
        
        # Show all attractions in an expandable dropdown
        with st.expander(f"🎯 View All {len(attraction_data)} Attractions & Activities"):
            for idx, attraction in enumerate(attraction_data, 1):
                attraction_name = attraction['name']
                address = attraction.get('address', 'Address not available')
                phone = attraction.get('phone', 'Phone not available')
                website = attraction.get('website', '')
                rating = attraction.get('rating', 'N/A')
                total_ratings = attraction.get('total_ratings', 0)
                hours = attraction.get('hours', 'Hours not available')
                review_snippet = attraction.get('review_snippet', 'No reviews available')
                google_maps_url = attraction.get('google_maps_url', '#')
                category = attraction.get('category', '📍 Point of Interest')
                photo_url = attraction.get('photo_url', '')
                source = attraction.get('source', 'Google Places API')
                
                st.markdown(f"""
                ### {idx}. {category} {attraction_name}
                
                **⭐ Rating:** {rating}/5 ({total_ratings} reviews)  
                **📍 Address:** {address}  
                **📞 Phone:** {phone}  
                **🕒 Hours:** {hours}  
                
                **📝 Visitor Review:** "{review_snippet}"
                
                **🔗 Links:**  
                • **[Official Website]({website})** - Tickets, info, booking  
                • **[View on Google Maps]({google_maps_url})** - Directions, photos, reviews
                
                **📊 Source:** {source}
                """)
                
                # Show photo if available
                if photo_url:
                    st.image(photo_url, width=300, caption=f"{attraction_name}")
                
                st.markdown("---")
    else:
        st.info("🎯 Attractions powered by Google Places API")

    # Display live events during the trip
    st.markdown('<div class="section-header">🎉 Live Events During Your Trip</div>', unsafe_allow_html=True)
    if live_events:
        st.write(f"**📅 Events from {departure_date} to {return_date}**")
        
        # Create selectbox for events
        event_options = [f"{idx}. {event.get('name', 'Unknown Event')[:80]}..." if len(event.get('name', '')) > 80 else f"{idx}. {event.get('name', 'Unknown Event')}" for idx, event in enumerate(live_events, 1)]
        selected_event_idx = st.selectbox("🎪 Select an event to view details:", range(len(event_options)), format_func=lambda x: event_options[x])
        
        if selected_event_idx is not None:
            event = live_events[selected_event_idx]
            event_title = event.get('name', 'No title available')
            event_snippet = event.get('description', 'No description available')
            event_link = event.get('website', '#')
            event_category = event.get('category', 'Event')
            event_date = event.get('date', 'Date TBA')
            event_icon = event.get('icon', '🎪')
            
            # Determine link type and provide specific guidance
            if any(keyword in event_link.lower() for keyword in ['ticketmaster', 'eventbrite', 'stubhub', 'tickets.com', 'buy', 'purchase', 'book']):
                link_type = "🎫 **Ticket Booking Site** - Purchase tickets directly for this event"
                link_text = "Buy Tickets"
            elif any(keyword in event_link.lower() for keyword in ['facebook.com', 'instagram.com', 'twitter.com']):
                link_type = "📱 **Social Media** - Follow event updates and see attendee discussions"
                link_text = "View Social Media"
            elif any(keyword in event_link.lower() for keyword in ['venue', 'theater', 'stadium', 'arena', 'club']):
                link_type = "🏟️ **Venue Website** - Venue info, directions, parking, and possibly tickets"
                link_text = "Visit Venue Website"
            elif any(keyword in event_link.lower() for keyword in ['official', '.gov', 'festival']):
                link_type = "🏛️ **Official Event Website** - Official info, schedules, lineup, and tickets"
                link_text = "Visit Official Event Site"
            else:
                # Use the link type from the event data if available
                link_type = event.get('link_type', "ℹ️ **Event Information** - Details about this event")
                link_text = event.get('link_text', "Get Event Details")
            
            st.markdown(f"""
            ### {selected_event_idx + 1}. {event_icon} {event_title}
            
            **🎭 Category:** {event_category}  
            **📅 Date:** {event_date}  
            **📄 Description:** {event_snippet}  
            
            **🔗 Link Type:** {link_type}
            
            **[{link_text}]({event_link})**
            """)
            st.markdown("---")
    else:
        st.info("🎉 Live events powered by Google Search")

    # Display local information with summaries and dropdowns
    st.markdown('<div class="section-header">ℹ️ Local Travel Information (Quick Summaries)</div>', unsafe_allow_html=True)
    if local_info:
        for info in local_info:
            icon = info.get('icon', 'ℹ️')
            category = info.get('category', 'Information')
            summary = info.get('summary', 'No summary available')
            sources = info.get('sources', [])
            
            # Display brief summary
            st.markdown(f"### {icon} {category}")
            st.write(summary)
            
            # Dropdown with detailed information and sources
            with st.expander(f"� More details about {category.lower()}"):
                full_description = info.get('full_description', summary)
                st.write(full_description)
                
                if sources:
                    st.markdown("**Sources:**")
                    for source in sources:
                        source_title = source.get('title', 'Source')
                        source_link = source.get('link', '#')
                        st.markdown(f"• [{source_title}]({source_link})")
            
            st.markdown("---")
    else:
        st.info("ℹ️ Local information powered by Google Search")

    st.markdown('<div class="section-header">🗺️ Your Personalized Itinerary</div>', unsafe_allow_html=True)
    st.markdown(itinerary.content, unsafe_allow_html=True)

    st.success("✅ Travel plan generated successfully!")



