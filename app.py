import streamlit as st
import google.generativeai as genai
import pandas as pd
from gtts import gTTS
import os
from io import BytesIO
import hashlib
import json
import re

import plotly.express as px
from datetime import datetime
import os

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="CoachBot AI",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ---------------- CUSTOM CSS ----------------
def load_custom_css():
    st.markdown("""
    <style>
        /* Modern Gradient Background */
        .stApp {
            background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        }
        
        /* Main Header - Glass Morphism */
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 3rem;
            border-radius: 20px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
            box-shadow: 0 20px 40px rgba(102, 126, 234, 0.3);
            backdrop-filter: blur(10px);
            border: 2px solid rgba(255, 255, 255, 0.1);
        }
        
        .main-header h1 {
            font-size: 3rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            font-weight: 800;
            letter-spacing: -1px;
        }
        
        .main-header h2 {
            font-size: 2.5rem;
            margin-bottom: 0.5rem;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
            font-weight: 700;
        }
        
        /* Metric Cards - Modern Card Design */
        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 2rem;
            border-radius: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.1);
            margin: 15px 0;
            border: 1px solid rgba(255, 255, 255, 0.5);
            transition: all 0.3s ease;
        }
        
        .metric-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 40px rgba(0,0,0,0.2);
        }
        
        .metric-card h3 {
            color: #667eea;
            margin-bottom: 1rem;
            font-size: 1.8rem;
        }
        
        /* BMI Results */
        .bmi-result {
            padding: 2.5rem;
            border-radius: 20px;
            margin: 1.5rem 0;
            text-align: center;
            font-size: 1.5rem;
        }
        
        .bmi-underweight { 
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); 
            border-left: 8px solid #ffc107; 
            box-shadow: 0 10px 30px rgba(255, 193, 7, 0.3);
        }
        
        .bmi-normal { 
            background: linear-gradient(135deg, #d4edda 0%, #95e1d3 100%); 
            border-left: 8px solid #28a745; 
            box-shadow: 0 10px 30px rgba(40, 167, 69, 0.3);
        }
        
        .bmi-overweight { 
            background: linear-gradient(135deg, #fff3cd 0%, #ffeaa7 100%); 
            border-left: 8px solid #ffc107; 
            box-shadow: 0 10px 30px rgba(255, 193, 7, 0.3);
        }
        
        .bmi-obese { 
            background: linear-gradient(135deg, #f8d7da 0%, #ffcccc 100%); 
            border-left: 8px solid #dc3545; 
            box-shadow: 0 10px 30px rgba(220, 53, 69, 0.3);
        }
        
        /* Streamlit Elements Styling */
        .stButton>button {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 0.75rem 1.5rem;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1rem;
            transition: all 0.3s ease;
            box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            width: 100%;
        }
        
        .stButton>button:hover {
            transform: translateY(-2px);
            box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
        }
        
        .stTextInput>div>div>input,
        .stTextArea>div>div>textarea,
        .stNumberInput>div>div>input,
        .stSelectbox>div>div>select {
            background: rgba(255, 255, 255, 0.95);
            border: 2px solid #667eea;
            border-radius: 12px;
            padding: 12px;
            font-size: 1rem;
        }
        
        .stTextInput>div>div>input:focus,
        .stTextArea>div>div>textarea:focus,
        .stNumberInput>div>div>input:focus,
        .stSelectbox>div>div>select:focus {
            border-color: #764ba2;
            box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.2);
        }
        
        /* Info/Success/Warning/Error Boxes */
        .stAlert {
            border-radius: 15px !important;
            border-left: 6px solid !important;
            box-shadow: 0 5px 15px rgba(0,0,0,0.1) !important;
            backdrop-filter: blur(10px) !important;
        }
        
        /* Sidebar Enhancement */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #667eea 0%, #764ba2 100%) !important;
        }
        
        [data-testid="stSidebar"] .css-17lntkn {
            background: transparent;
        }
        
        /* Metric Value Styling */
        [data-testid="stMetricValue"] {
            color: #667eea !important;
            font-weight: 700 !important;
        }
        
        [data-testid="stMetricLabel"] {
            color: #666 !important;
            font-weight: 600 !important;
        }
        
        /* Chat Interface */
        .chat-message-user {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 1.5rem;
            border-radius: 20px;
            margin: 1rem 0;
            box-shadow: 0 5px 15px rgba(102, 126, 234, 0.3);
        }
        
        .chat-message-assistant {
            background: rgba(255, 255, 255, 0.95);
            padding: 1.5rem;
            border-radius: 20px;
            margin: 1rem 0;
            border-left: 5px solid #667eea;
            box-shadow: 0 5px 15px rgba(0, 0, 0, 0.1);
        }
        
        /* Generated Plan Container */
        .generated-plan {
            background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
            padding: 3rem;
            border-radius: 25px;
            margin: 2rem 0;
            box-shadow: 0 15px 40px rgba(0,0,0,0.1);
            border: 2px solid rgba(102, 126, 234, 0.2);
        }
        
        /* Animated Elements */
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.05); }
        }
        
        .pulse-animation {
            animation: pulse 2s infinite;
        }
        
        /* Section Headers */
        .section-header {
            background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            background-clip: text;
            font-size: 2rem;
            font-weight: 700;
            margin: 2rem 0 1rem 0;
        }
        
        /* Cards Grid */
        .card-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 1.5rem;
            margin: 1.5rem 0;
        }
        
        /* Custom Scrollbar */
        ::-webkit-scrollbar {
            width: 12px;
        }
        
        ::-webkit-scrollbar-track {
            background: #f1f1f1;
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 10px;
        }
        
        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(135deg, #764ba2 0%, #667eea 100%);
        }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()

# ---------------- API CONFIGURATION ----------------
@st.cache_resource
def initialize_gemini():
    """Initialize Gemini API with Streamlit secrets"""
    try:
        # Try multiple possible secret names
        api_key = st.secrets.get("GEMINI_API_KEY", None)
        if not api_key:
            api_key = st.secrets.get("GOOGLE_API_KEY", None)
        if not api_key:
            api_key = st.secrets.get("gemini_api_key", None)
        
        if not api_key:
            st.error("❌ **API Key Not Found!**")
            st.error("Please add your GEMINI_API_KEY to Streamlit secrets.")
            st.info("Go to: Settings → Secrets → Add: GEMINI_API_KEY = 'your-key'")
            return None
        
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash-exp",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 4000
            }
        )
        
        # Test the model
        test_response = model.generate_content("Test")
        return model
        
    except Exception as e:
        st.error(f"❌ **API Initialization Error:** {str(e)}")
        st.error("Please check your API key configuration.")
        return None

model = initialize_gemini()

# Check if model is available
if not model:
    st.warning("⚠️ **AI Features Limited**")
    st.info("Some features require a valid Google Generative AI API key.")

# ---------------- SESSION STATE ----------------
if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'workouts_generated' not in st.session_state:
    st.session_state.workouts_generated = 0
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []

# ---------------- SPORT CONFIGURATION ----------------
SPORT_CONFIG = {
    "Football": {
        "icon": "⚽",
        "positions": ["Forward", "Midfielder", "Defender", "Goalkeeper"],
        "skills": ["Ball Control", "Passing", "Shooting", "Dribbling", "Defense", "Speed"],
        "injuries": ["Ankle Sprain", "Knee Injury", "Hamstring", "Concussion", "Groin Strain"]
    },
    "Cricket": {
        "icon": "🏏",
        "positions": ["Batsman", "Bowler", "All-rounder", "Wicket-keeper"],
        "skills": ["Batting", "Bowling", "Fielding", "Catching", "Running"],
        "injuries": ["Shoulder Injury", "Back Pain", "Ankle Sprain", "Elbow Injury"]
    },
    "Basketball": {
        "icon": "🏀",
        "positions": ["Point Guard", "Shooting Guard", "Small Forward", "Power Forward", "Center"],
        "skills": ["Shooting", "Dribbling", "Passing", "Rebounding", "Defense"],
        "injuries": ["Knee Injury", "Ankle Sprain", "Wrist Injury", "Back Pain"]
    },
    "Athletics": {
        "icon": "🏃‍♂️",
        "positions": ["Sprinter", "Distance Runner", "Jumper", "Thrower"],
        "skills": ["Speed", "Endurance", "Power", "Technique", "Strength"],
        "injuries": ["Hamstring", "Shin Splints", "Knee Pain", "Stress Fracture"]
    }
}

# ---------------- BMI CALCULATOR ----------------
def calculate_bmi(weight, height_cm):
    """Calculate BMI from weight (kg) and height (cm)"""
    height_m = height_cm / 100
    bmi = weight / (height_m ** 2)
    return round(bmi, 1)

def get_bmi_category(bmi):
    """Get BMI category and color class"""
    if bmi < 18.5:
        return "Underweight", "bmi-underweight"
    elif 18.5 <= bmi < 25:
        return "Normal Weight", "bmi-normal"
    elif 25 <= bmi < 30:
        return "Overweight", "bmi-overweight"
    else:
        return "Obese", "bmi-obese"

def display_bmi_calculator():
    """Display BMI Calculator interface"""
    st.subheader("📊 BMI Calculator")
    
    col1, col2, col3 = st.columns([1, 1, 1])
    
    with col1:
        weight = st.number_input("Weight (kg)", min_value=20.0, max_value=200.0, value=70.0, step=0.5)
    
    with col2:
        height = st.number_input("Height (cm)", min_value=100, max_value=250, value=170, step=1)
    
    with col3:
        age = st.number_input("Age", min_value=10, max_value=30, value=15, step=1)
    
    if st.button("Calculate BMI", use_container_width=True):
        bmi = calculate_bmi(weight, height)
        category, css_class = get_bmi_category(bmi)
        
        st.markdown(f"""
        <div class="bmi-result {css_class}">
            <h3>Your BMI: {bmi}</h3>
            <p><strong>Category:</strong> {category}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Health recommendations based on BMI
        if bmi < 18.5:
            st.warning("""
            💡 **Recommendations:**
            - Increase calorie intake with nutrient-dense foods
            - Focus on protein and complex carbohydrates
            - Include strength training to build muscle mass
            - Consult a nutritionist for personalized meal plan
            """)
        elif 18.5 <= bmi < 25:
            st.success("""
            ✅ **Great job!** You're in the healthy weight range.
            - Maintain balanced nutrition
            - Continue regular physical activity
            - Focus on sport-specific training
            - Stay hydrated and get adequate sleep
            """)
        elif 25 <= bmi < 30:
            st.info("""
            💡 **Recommendations:**
            - Aim for gradual weight loss (0.5-1 kg per week)
            - Increase cardiovascular activity
            - Focus on portion control and balanced meals
            - Include both cardio and strength training
            """)
        else:
            st.error("""
            ⚠️ **Recommendations:**
            - Consult a healthcare provider before starting intensive training
            - Focus on sustainable lifestyle changes
            - Work with a fitness professional for safe exercise program
            - Prioritize nutrition education and portion control
            """)
        
        # Store BMI in session state
        st.session_state.user_profile.update({
            'weight': weight,
            'height': height,
            'age': age,
            'bmi': bmi,
            'bmi_category': category
        })

# ---------------- SIDEBAR NAVIGATION ----------------
def sidebar_navigation():
    with st.sidebar:
        st.markdown('<div class="main-header"><h2>🏆 CoachBot AI</h2></div>', unsafe_allow_html=True)
        st.markdown("---")
        
        st.subheader("📊 Navigation")
        pages = ["Dashboard", "BMI Calculator", "Profile Setup", "Training Plan", "Nutrition", "AI Coach"]
        
        for page in pages:
            icon = "🏠" if page == "Dashboard" else "⚖️" if page == "BMI Calculator" else "👤" if page == "Profile Setup" else "💪" if page == "Training Plan" else "🥗" if page == "Nutrition" else "💬"
            if st.button(f"{icon} {page}", key=f"nav_{page}"):
                st.session_state.page = page
                st.rerun()
        
        st.markdown("---")
        
        # User Stats
        st.subheader("📈 Your Stats")
        st.metric("Plans Generated", st.session_state.workouts_generated)
        if 'bmi' in st.session_state.user_profile:
            st.metric("BMI", st.session_state.user_profile['bmi'])
        
        st.markdown("---")
        st.markdown("💡 *Your AI-powered fitness coach for youth athletes!*")

sidebar_navigation()

# ---------------- PAGE FUNCTIONS ----------------

def dashboard_page():
    st.markdown('<div class="main-header"><h1>🏠 Welcome to CoachBot AI!</h1></div>', unsafe_allow_html=True)
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 Plans Generated", st.session_state.workouts_generated)
    with col2:
        st.metric("🎯 Profile Status", "✅ Complete" if st.session_state.user_profile else "⏳ Pending")
    with col3:
        st.metric("🏃 Sport", st.session_state.user_profile.get('sport', 'N/A') if st.session_state.user_profile else 'N/A')
    with col4:
        st.metric("💪 Fitness Level", st.session_state.user_profile.get('fitness_level', 'N/A') if st.session_state.user_profile else 'N/A')
    
    st.markdown("---")
    
    # Welcome Message
    col1, col2 = st.columns([2, 1])
    with col1:
        st.info("""
        👋 **Welcome to your AI-Powered Fitness Coach!**
        
        CoachBot AI uses advanced AI to help you:
        - 📊 Calculate and understand your BMI
        - 💪 Generate personalized AI workout plans
        - 🥗 Create AI-tailored nutrition plans
        - 🏥 Provide AI-driven recovery strategies
        - 🧠 Offer AI-powered mental training
        - 💬 Chat with your AI coach anytime
        
        **All plans and advice are generated by AI based on your unique profile!**
        """)
    
    with col2:
        st.success("""
        🚀 **Quick Start Guide:**
        
        1. Calculate your BMI
        2. Set up your profile
        3. Generate AI training plans
        4. Get AI nutrition advice
        5. Chat with AI Coach
        """)
    
    st.markdown("---")
    
    # Featured Features
    st.subheader("✨ Start Your Journey")
    
    features_grid = {
        "📊 BMI Calculator": "Understand your body composition",
        "👤 Profile Setup": "Customize your athletic profile",
        "💪 AI Training": "Get personalized workout plans",
        "🥗 AI Nutrition": "Eat right for your goals",
        "🏥 AI Recovery": "Stay injury-free",
        "🧠 Mental Training": "Build mental toughness",
        "🎯 Tactical Tips": "Master your sport",
        "💬 AI Coach Chat": "24/7 guidance"
    }
    
    cols = st.columns(4)
    for i, (feature, description) in enumerate(features_grid.items()):
        with cols[i % 4]:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{feature}</h3>
                <p>{description}</p>
            </div>
            """, unsafe_allow_html=True)

def bmi_calculator_page():
    st.markdown('<div class="main-header"><h1>⚖️ BMI Calculator</h1></div>', unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Display BMI Calculator
    display_bmi_calculator()
    
    st.markdown("---")
    
    # BMI Information
    st.subheader("📚 Understanding BMI")
    
    st.markdown("""
    **Body Mass Index (BMI)** is a measure of body fat based on height and weight.
    
    **BMI Categories:**
    - **Underweight**: BMI < 18.5
    - **Normal Weight**: 18.5 ≤ BMI < 25
    - **Overweight**: 25 ≤ BMI < 30
    - **Obese**: BMI ≥ 30
    
    **Note for Athletes:**
    BMI may not accurately reflect body composition for athletes with high muscle mass.
    Consider other factors like waist circumference, body fat percentage, and overall fitness level.
    """)
    
    # BMI Chart
    st.subheader("📊 BMI Reference Chart")
    
    bmi_data = pd.DataFrame({
        'Category': ['Underweight', 'Normal', 'Overweight', 'Obese'],
        'BMI Range': ['< 18.5', '18.5 - 24.9', '25 - 29.9', '≥ 30'],
        'Color': ['#ffc107', '#28a745', '#ffc107', '#dc3545']
    })
    
    st.dataframe(bmi_data, use_container_width=True, hide_index=True)

def profile_setup_page():
    st.markdown('<div class="main-header"><h1>👤 Profile Setup</h1></div>', unsafe_allow_html=True)
    
    # Check if BMI data exists
    if 'bmi' not in st.session_state.user_profile:
        st.warning("⚠️ Please calculate your BMI first in the BMI Calculator section!")
        st.info("💡 Go to the BMI Calculator page and calculate your BMI before setting up your profile.")
        return
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🏆 Sport Details")
        sport = st.selectbox("Select Sport", list(SPORT_CONFIG.keys()))
        if sport:
            sport_config = SPORT_CONFIG[sport]
            position = st.selectbox("Position/Role", sport_config["positions"])
            
            st.subheader("📊 Fitness Information")
            experience = st.selectbox("Training Experience", 
                ["0-6 months", "6-12 months", "1-2 years", "2+ years"])
            fitness_level = st.selectbox("Current Fitness Level", 
                ["Beginner", "Intermediate", "Advanced"])
            frequency = st.selectbox("Training Frequency", 
                ["2 days/week", "3 days/week", "4 days/week", "5 days/week"])
            duration = st.selectbox("Session Duration", 
                ["30 minutes", "45 minutes", "60 minutes", "90 minutes"])
    
    with col2:
        st.subheader("🎯 Goals")
        goal = st.selectbox("Primary Goal", 
            ["Improve overall fitness", "Build strength", "Increase endurance", 
             "Lose weight", "Gain muscle", "Recover from injury", "Improve technique"])
        
        intensity = st.selectbox("Intensity Preference", 
            ["Low", "Moderate", "High", "Very High"])
        
        st.subheader("🏥 Health Information")
        injury = st.text_area("Injury History (if any)", 
            placeholder="Describe any past or current injuries")
        limitations = st.text_input("Physical Limitations", 
            placeholder="Any exercises to avoid")
        
        st.subheader("🥗 Nutrition Preferences")
        diet = st.selectbox("Diet Type", 
            ["Balanced", "Vegetarian", "Vegan", "High Protein"])
        allergies = st.text_input("Food Allergies", 
            placeholder="Any food allergies")
    
    # Save Profile Button
    st.markdown("---")
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("💾 Save Profile", use_container_width=True):
            user_data = {
                'sport': sport,
                'position': position,
                'experience': experience,
                'fitness_level': fitness_level,
                'frequency': frequency,
                'duration': duration,
                'goal': goal,
                'intensity': intensity,
                'injury': injury,
                'limitations': limitations,
                'diet': diet,
                'allergies': allergies
            }
            
            # Merge with existing profile (BMI data)
            user_data.update(st.session_state.user_profile)
            
            st.session_state.user_profile = user_data
            st.success("✅ Profile saved successfully!")
            st.info("🎉 Now you can generate your personalized training plan!")

def generate_ai_plan(plan_type):
    """Generate AI-powered plan based on type"""
    if not model:
        st.error("❌ **AI Model Not Available**")
        st.error("Please configure your GEMINI_API_KEY to use AI-generated plans.")
        return
    
    profile = st.session_state.user_profile
    
    if not profile:
        st.error("❌ **Profile Not Found**")
        st.error("Please complete your profile setup first.")
        return
    
    try:
        # Create specialized prompt
        prompt = create_training_prompt(profile, plan_type)
        
        # Add additional instructions for better output
        prompt += "\n\nIMPORTANT: Make the output detailed, specific, and actionable. Use Markdown formatting with headers, bullet points, and proper structure."
        
        with st.spinner("🧠 AI Coach is creating your personalized plan..."):
            # Generate content
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                st.error("❌ **AI Generation Failed**")
                st.error("The AI did not return any content. Please try again.")
                return
            
            # Store the generated plan
            st.session_state.generated_plan = response.text
            st.session_state.workouts_generated += 1
            
            st.success("✅ **AI-Generated Plan Created Successfully!**")
            st.info("Your personalized plan is ready below.")
            st.rerun()
            
    except Exception as e:
        st.error(f"❌ **AI Generation Error:** {str(e)}")
        st.error("There was a problem generating your AI plan.")
        st.info(f"Error details: {type(e).__name__}")
        
        # Try one more time with simpler prompt
        try:
            simple_prompt = f"Create a {plan_type} plan for a {profile.get('sport', 'athlete')}."
            response = model.generate_content(simple_prompt)
            st.session_state.generated_plan = response.text
            st.session_state.workouts_generated += 1
            st.success("✅ Plan generated with fallback method!")
            st.rerun()
        except:
            st.error("❌ **Could not generate plan**")
            st.error("Please check your API key and try again.")

def training_plan_page():
    try:
        st.markdown('<div class="main-header"><h1>💪 AI Training Plan Generator</h1></div>', unsafe_allow_html=True)
        
        # Check if API is available
        if not model:
            st.error("❌ **AI Features Not Available**")
            st.error("This app requires a valid Google Generative AI API key.")
            st.info("All plans are AI-generated. The app cannot function without the API key.")
            return
        
        # Check if profile exists
        if not st.session_state.user_profile or 'sport' not in st.session_state.user_profile:
            st.warning("⚠️ Please set up your profile first!")
            st.info("💡 Go to the Profile Setup page and complete your profile.")
            return
        
        # Display current profile summary
        st.subheader("📋 Your Profile")
        profile = st.session_state.user_profile
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Sport", f"{SPORT_CONFIG.get(profile['sport'], {}).get('icon', '🏆')} {profile['sport']}")
            st.metric("Position", profile['position'])
        with col2:
            st.metric("Fitness Level", profile['fitness_level'])
            st.metric("Experience", profile['experience'])
        with col3:
            st.metric("BMI", f"{profile.get('bmi', 'N/A')}")
            st.metric("Goal", profile['goal'])
        
        st.markdown("---")
        
        st.info("🤖 **All plans are AI-generated based on your profile**")
        
        # Generate Options
        st.subheader("🎯 Generate Your AI Plan")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🏋️ AI Workout Plan", use_container_width=True):
                generate_ai_plan("workout")
        
        with col2:
            if st.button("🥗 AI Nutrition Plan", use_container_width=True):
                generate_ai_plan("nutrition")
        
        with col3:
            if st.button("🏥 AI Recovery Plan", use_container_width=True):
                generate_ai_plan("recovery")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🧠 AI Mental Training", use_container_width=True):
                generate_ai_plan("mental")
        
        with col2:
            if st.button("🎯 AI Tactical Tips", use_container_width=True):
                generate_ai_plan("tactical")
        
        # Display generated plan
        if 'generated_plan' in st.session_state and st.session_state.generated_plan:
            st.markdown("---")
            st.markdown('<div class="main-header"><h2>🤖 Your AI-Generated Personalized Plan</h2></div>', unsafe_allow_html=True)
            st.markdown(st.session_state.generated_plan)
            
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🔄 Generate New Plan", use_container_width=True):
                    st.session_state.generated_plan = None
                    st.rerun()
    except Exception as e:
        st.error(f"Error in training plan page: {str(e)}")
        return

def nutrition_page():
    try:
        st.markdown('<div class="main-header"><h1>🥗 Nutrition Guide</h1></div>', unsafe_allow_html=True)
        
        if not st.session_state.user_profile:
            st.warning("⚠️ Please set up your profile first!")
            return
        
        profile = st.session_state.user_profile
        
        st.subheader("📊 Your Nutritional Needs")
        
        # Calculate daily calories based on BMI and activity
        weight = profile.get('weight', 65)
        height = profile.get('height', 170)
        age = profile.get('age', 15)
        gender = profile.get('gender', 'Male')
        
        # Simple BMR calculation
        if gender == "Male":
            bmr = 10 * weight + 6.25 * height - 5 * age + 5
        else:
            bmr = 10 * weight + 6.25 * height - 5 * age - 161
        
        activity_multiplier = {
            "2 days/week": 1.375,
            "3 days/week": 1.55,
            "4 days/week": 1.725,
            "5 days/week": 1.9
        }
        
        frequency = profile.get('frequency', '3 days/week')
        tdee = bmr * activity_multiplier.get(frequency, 1.55)
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("🔥 BMR", f"{int(bmr)} cal")
        with col2:
            st.metric("⚡ Daily Calories", f"{int(tdee)} cal")
        with col3:
            st.metric("🥩 Protein", f"{int((tdee * 0.3) / 4)}g")
        with col4:
            st.metric("🍞 Carbs", f"{int((tdee * 0.45) / 4)}g")
        
        st.markdown("---")
        
        # Meal Suggestions
        st.subheader("🍽️ Daily Meal Structure")
        
        meals = [
            {
                "name": "🌅 Breakfast",
                "time": "7:00 AM",
                "calories": int(tdee * 0.25),
                "suggestions": [
                    "Oatmeal with berries and nuts",
                    "Greek yogurt with honey and fruit",
                    "Whole grain toast with eggs",
                    "Smoothie with protein powder, banana, and spinach"
                ]
            },
            {
                "name": "🥪 Lunch",
                "time": "12:30 PM",
                "calories": int(tdee * 0.30),
                "suggestions": [
                    "Grilled chicken salad with quinoa",
                    "Turkey sandwich on whole grain bread",
                    "Brown rice with vegetables and lean protein",
                    "Pasta with tomato sauce and ground turkey"
                ]
            },
            {
                "name": "🍎 Snack",
                "time": "3:30 PM",
                "calories": int(tdee * 0.15),
                "suggestions": [
                    "Apple with almond butter",
                    "Greek yogurt with granola",
                    "Protein shake",
                    "Mixed nuts and dried fruits"
                ]
            },
            {
                "name": "🍝 Dinner",
                "time": "7:00 PM",
                "calories": int(tdee * 0.30),
                "suggestions": [
                    "Grilled fish with vegetables",
                    "Lean beef stir-fry with brown rice",
                    "Chicken breast with sweet potato",
                    "Vegetable curry with lentils"
                ]
            }
        ]
        
        for meal in meals:
            st.markdown(f"""
            <div class="metric-card">
                <h3>{meal['name']} - {meal['time']}</h3>
                <p><strong>Calories:</strong> {meal['calories']}</p>
                <p><strong>Suggestions:</strong></p>
                <ul>
        """, unsafe_allow_html=True)
            
            for suggestion in meal['suggestions']:
                st.markdown(f"<li>{suggestion}</li>", unsafe_allow_html=True)
            
            st.markdown("</ul></div>", unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Hydration
        st.subheader("💧 Hydration Guidelines")
        st.info("""
        💧 **Daily Water Intake:** 2-3 liters
        
        **Additional fluid needs during training:**
        - Before training: 500ml (2 hours before)
        - During training: 150-200ml every 15-20 minutes
        - After training: 500-750ml for recovery
        
        **Signs of dehydration:**
        - Dark urine
        - Dry mouth
        - Fatigue
        - Dizziness
        """)
    except Exception as e:
        st.error(f"Error in nutrition page: {str(e)}")
        return

def ai_coach_page():
    st.markdown('<div class="main-header"><h1>💬 AI Coach Chat</h1></div>', unsafe_allow_html=True)
    
    # Check if API is configured
    if not model:
        st.error("❌ **AI Coach Not Available**")
        st.error("This app requires a valid Google Generative AI API key to function.")
        st.info("""
        **To enable AI features:**
        1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Add it to Streamlit secrets as `GEMINI_API_KEY`
        3. Restart the app
        """)
        return
    
    # Chat History Display
    chat_container = st.container()
    
    with chat_container:
        if not st.session_state.chat_history:
            st.info("""
            👋 **Hello! I'm your AI Coach. Ask me anything about:**
            
            - Training techniques and exercises
            - Nutrition and meal planning
            - Injury prevention and recovery
            - Mental training and motivation
            - Sport-specific strategies
            - Performance improvement tips
            
            **How can I help you today?**
            """)
        else:
            for message in st.session_state.chat_history:
                if message['role'] == 'user':
                    st.markdown(f"""
                    <div class="chat-message-user">
                        <strong>You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div class="chat-message-assistant">
                        <strong>🏋️ CoachBot:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # User Input
    user_question = st.text_area("Ask your question:", 
        placeholder="e.g., How can I improve my sprint speed?", height=100)
    
    col1, col2 = st.columns([4, 1])
    with col2:
        if st.button("Send 📤", use_container_width=True):
            if user_question:
                # Add user message
                st.session_state.chat_history.append({"role": "user", "content": user_question})
                
                # Create enhanced context
                user_profile = st.session_state.user_profile if st.session_state.user_profile else 'New user'
                context = f"""
                You are a friendly, knowledgeable, and encouraging youth sports coach and fitness expert.
                
                USER PROFILE: {user_profile}
                
                USER'S QUESTION: {user_question}
                
                INSTRUCTIONS:
                1. Provide helpful, accurate, and age-appropriate advice
                2. Be encouraging and motivating
                3. Use emojis to make it engaging
                4. Keep responses comprehensive but not too long
                5. If relevant, reference their profile information (sport, position, goals, etc.)
                6. Provide actionable and practical tips
                7. Use proper formatting with bullet points and headers where appropriate
                
                Now, answer the user's question thoroughly and helpfully:
                """
                
                try:
                    with st.spinner("🏋️ CoachBot is thinking..."):
                        response = model.generate_content(context)
                        
                        if not response or not response.text:
                            raise Exception("No response from AI")
                        
                        ai_response = response.text
                    
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    st.success("✅ Response generated!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ **AI Error:** {str(e)}")
                    st.error("There was a problem generating the response.")
                    st.info(f"Error type: {type(e).__name__}")
                    
                    # Remove the failed user message
                    st.session_state.chat_history.pop()
                    st.warning("Please try again or check your API configuration.")
            else:
                st.warning("Please enter a question before sending.")
    
    # Quick Questions
    st.markdown("---")
    st.subheader("💡 Quick Questions")
    
    quick_questions = [
        "How can I prevent sports injuries?",
        "What should I eat before training?",
        "How can I improve my endurance?",
        "What's the best way to recover after a workout?",
        "How do I stay motivated to train?"
    ]
    
    cols = st.columns(5)
    for i, question in enumerate(quick_questions):
        with cols[i]:
            if st.button(question, key=f"quick_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": question})
                
                user_profile = st.session_state.user_profile if st.session_state.user_profile else 'New user'
                context = f"""
                You are a friendly youth sports coach.
                Answer this question comprehensively: {question}
                
                User Profile: {user_profile}
                
                Be encouraging, practical, and age-appropriate. Use emojis.
                """
                
                try:
                    with st.spinner("🏋️ CoachBot is thinking..."):
                        response = model.generate_content(context)
                        
                        if not response or not response.text:
                            raise Exception("No response from AI")
                        
                        ai_response = response.text
                    
                    st.session_state.chat_history.append({"role": "assistant", "content": ai_response})
                    st.success("✅ Response generated!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ **AI Error:** {str(e)}")
                    st.session_state.chat_history.pop()
                    st.warning("Please try again.")

# ---------------- MAIN APP LOGIC ----------------
def main():
    try:
        # Display the current page
        if st.session_state.page == 'Dashboard':
            dashboard_page()
        elif st.session_state.page == 'BMI Calculator':
            bmi_calculator_page()
        elif st.session_state.page == 'Profile Setup':
            profile_setup_page()
        elif st.session_state.page == 'Training Plan':
            training_plan_page()
        elif st.session_state.page == 'Nutrition':
            nutrition_page()
        elif st.session_state.page == 'AI Coach':
            ai_coach_page()
    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        st.info("Please refresh the page and try again.")

if __name__ == "__main__":
    main()
