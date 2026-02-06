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
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib import colors

st.set_page_config(
    page_title="CoachBot AI",
    page_icon="🏆",
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_custom_css():
    st.markdown("""
    <style>
        .main-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            padding: 2rem;
            border-radius: 15px;
            color: white;
            text-align: center;
            margin-bottom: 2rem;
        }
        .metric-card {
            background: white;
            padding: 1.5rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
            margin: 10px 0;
        }
        .bmi-result {
            padding: 1.5rem;
            border-radius: 10px;
            margin: 1rem 0;
        }
        .bmi-underweight { background: #fff3cd; border-left: 5px solid #ffc107; }
        .bmi-normal { background: #d4edda; border-left: 5px solid #28a745; }
        .bmi-overweight { background: #fff3cd; border-left: 5px solid #ffc107; }
        .bmi-obese { background: #f8d7da; border-left: 5px solid #dc3545; }
    </style>
    """, unsafe_allow_html=True)

load_custom_css()


@st.cache_resource
def initialize_gemini():
    """Initialize Gemini API with Streamlit secrets"""
    try:
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
            model_name="gemini-2.5-flash-exp",
            generation_config={
                "temperature": 0.7,
                "top_p": 0.8,
                "top_k": 40,
                "max_output_tokens": 8192  # Increased from 4000 to prevent truncation
            }
        )
        
        test_response = model.generate_content("Test")
        return model
        
    except Exception as e:
        st.error(f"❌ **API Initialization Error:** {str(e)}")
        st.error("Please check your API key configuration.")
        return None

model = initialize_gemini()


if not model:
    st.error("⚠️ **AI Features Not Available**")
    st.error("The app requires a valid Google Generative AI API key to function.")
    st.info("Please add your GEMINI_API_KEY to Streamlit secrets and restart the app.")


if 'page' not in st.session_state:
    st.session_state.page = 'Dashboard'
if 'user_profile' not in st.session_state:
    st.session_state.user_profile = {}
if 'workouts_generated' not in st.session_state:
    st.session_state.workouts_generated = 0
if 'chat_history' not in st.session_state:
    st.session_state.chat_history = []
if 'generated_plan' not in st.session_state:
    st.session_state.generated_plan = None

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
      
        st.session_state.user_profile.update({
            'weight': weight,
            'height': height,
            'age': age,
            'bmi': bmi,
            'bmi_category': category
        })


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
        
      
        st.subheader("📈 Your Stats")
        st.metric("Plans Generated", st.session_state.workouts_generated)
        if 'bmi' in st.session_state.user_profile:
            st.metric("BMI", st.session_state.user_profile['bmi'])
        
        st.markdown("---")
        st.markdown("💡 *Your AI-powered fitness coach for youth athletes!*")

sidebar_navigation()

def create_training_prompt(user_data, focus_area="general"):
    """Create specialized prompt based on focus area"""
    
    prompts = {
        "workout": f"""
        You are an elite youth sports coach specializing in {user_data['sport']}.
        
        ATHLETE PROFILE:
        - Age: {user_data['age']} years
        - Sport: {user_data['sport']}
        - Position: {user_data['position']}
        - Fitness Level: {user_data.get('fitness_level', 'Beginner')}
        - Experience: {user_data.get('experience', '0-6 months')}
        - BMI: {user_data.get('bmi', 'N/A')} ({user_data.get('bmi_category', 'N/A')})
        - Training Goal: {user_data.get('goal', 'Improve overall fitness')}
        - Injury History: {user_data.get('injury', 'None')}
        - Training Frequency: {user_data.get('frequency', '3 days/week')}
        - Session Duration: {user_data.get('duration', '60 minutes')}
        
        TASK: Generate a comprehensive workout plan including:
        1. Warm-up routine (10-15 minutes)
        2. Main workout exercises with sets, reps, and rest periods
        3. Cool-down and stretching (10 minutes)
        4. Safety precautions and form tips
        5. Intensity guidelines (1-10 scale)
        
        Make it age-appropriate, safe, and motivating. Use emojis and bullet points. Format in tables. Provide detailed and comprehensive information.
        """,
        
        "nutrition": f"""
        You are a certified sports nutritionist for young athletes.
        
        ATHLETE PROFILE:
        - Age: {user_data['age']} years
        - Sport: {user_data['sport']}
        - Position: {user_data['position']}
        - Weight: {user_data.get('weight', 65)} kg
        - Height: {user_data.get('height', 170)} cm
        - BMI: {user_data.get('bmi', 'N/A')} ({user_data.get('bmi_category', 'N/A')})
        - Diet Type: {user_data.get('diet', 'Balanced')}
        - Allergies: {user_data.get('allergies', 'None')}
        - Training Goal: {user_data.get('goal', 'Improve performance')}
        
        TASK: Create a personalized nutrition plan including:
        1. Daily caloric needs estimation
        2. Macronutrient breakdown (protein, carbs, fats)
        3. Pre-workout meal suggestions
        4. Post-workout recovery nutrition
        5. Hydration guidelines
        6. Sample one-day meal plan
        7. Healthy snack options
        
        Consider age-appropriate nutritional needs and BMI status. Format in tables. Provide detailed and comprehensive information.
        """,
        
        "recovery": f"""
        You are a sports rehabilitation specialist.
        
        ATHLETE PROFILE:
        - Age: {user_data['age']} years
        - Sport: {user_data['sport']}
        - Position: {user_data['position']}
        - Injury History: {user_data.get('injury', 'None')}
        - Current Limitations: {user_data.get('limitations', 'None')}
        
        TASK: Provide recovery and injury prevention strategies including:
        1. Pre-training injury prevention exercises
        2. Proper warm-up sequences
        3. Recovery techniques after workouts
        4. Stretching routines for {user_data['sport']}
        5. Warning signs to watch for
        6. When to seek medical attention
        7. Active recovery activities
        
        Prioritize safety and proper technique. Provide detailed and comprehensive information.
        """,
        
        "tactical": f"""
        You are an expert {user_data['sport']} coach with tactical expertise.
        
        ATHLETE PROFILE:
        - Age: {user_data['age']} years
        - Sport: {user_data['sport']}
        - Position: {user_data['position']}
        - Experience: {user_data.get('experience', 'Beginner')}
        - Skill Level: {user_data.get('fitness_level', 'Beginner')}
        
        TASK: Provide tactical coaching tips including:
        1. Position-specific responsibilities
        2. Decision-making drills
        3. Game intelligence tips
        4. Communication strategies
        5. Reading the game
        6. Mental preparation for competition
        
        Make it practical and easy to understand for young athletes. Provide detailed and comprehensive information.
        """,
        
        "mental": f"""
        You are a sports psychologist specializing in youth athletics.
        
        ATHLETE PROFILE:
        - Age: {user_data['age']} years
        - Sport: {user_data['sport']}
        - Position: {user_data['position']}
        - Experience: {user_data.get('experience', 'Beginner')}
        
        TASK: Provide mental training techniques including:
        1. Goal-setting strategies
        2. Visualization techniques
        3. Pre-competition routines
        4. Stress management tips
        5. Motivation and focus exercises
        6. Building confidence
        7. Handling pressure situations
        
        Make it age-appropriate and practical. Provide detailed and comprehensive information.
        """
    }
    
    return prompts.get(focus_area, prompts["workout"])

def create_pdf(plan_text, plan_type):
    """Create PDF from generated plan text"""
    pdf_buffer = BytesIO()
    doc = SimpleDocTemplate(pdf_buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#667eea'),
        alignment=TA_CENTER,
        spaceAfter=30
    )
    
    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=16,
        textColor=colors.HexColor('#764ba2'),
        spaceAfter=12,
        spaceBefore=20
    )
    
    body_style = ParagraphStyle(
        'CustomBody',
        parent=styles['BodyText'],
        fontSize=11,
        spaceAfter=12,
        leading=14
    )
    
    story = []
    
    # Title
    story.append(Paragraph(f"CoachBot AI - {plan_type} Plan", title_style))
    story.append(Spacer(1, 20))
    
    # Profile information
    profile = st.session_state.user_profile
    if profile:
        profile_data = [
            ["Sport", profile.get('sport', 'N/A')],
            ["Position", profile.get('position', 'N/A')],
            ["Age", f"{profile.get('age', 'N/A')} years"],
            ["Fitness Level", profile.get('fitness_level', 'N/A')],
            ["Goal", profile.get('goal', 'N/A')],
            ["BMI", f"{profile.get('bmi', 'N/A')} ({profile.get('bmi_category', 'N/A')})"],
        ]
        
        profile_table = Table(profile_data, colWidths=[2*inch, 4*inch])
        profile_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        
        story.append(Paragraph("Athlete Profile", heading_style))
        story.append(profile_table)
        story.append(Spacer(1, 30))
    
    # Plan content - Process markdown-style formatting
    story.append(Paragraph("Your Personalized Plan", heading_style))
    
    # Split text into paragraphs
    lines = plan_text.split('\n')
    for line in lines:
        line = line.strip()
        if line:
            # Convert markdown headers to PDF paragraphs
            if line.startswith('###'):
                text = line.replace('###', '').strip()
                story.append(Paragraph(text, heading_style))
            elif line.startswith('##'):
                text = line.replace('##', '').strip()
                story.append(Paragraph(text, heading_style))
            elif line.startswith('#'):
                text = line.replace('#', '').strip()
                story.append(Paragraph(text, title_style))
            elif line.startswith('-') or line.startswith('*'):
                # Bullet points
                text = line.replace('-', '').replace('*', '').strip()
                story.append(Paragraph(f"• {text}", body_style))
            elif line.startswith('|'):
                # Table row - skip for now, would need more complex parsing
                continue
            else:
                # Regular paragraph
                story.append(Paragraph(line, body_style))
    
    # Footer
    story.append(Spacer(1, 40))
    story.append(Paragraph("Generated by CoachBot AI", ParagraphStyle(
        'Footer',
        parent=styles['Normal'],
        fontSize=9,
        textColor=colors.gray,
        alignment=TA_CENTER
    )))
    
    doc.build(story)
    pdf_buffer.seek(0)
    return pdf_buffer

def generate_ai_plan(plan_type):
    """Generate AI-powered plan based on type"""
    if not model:
        st.error("❌ **AI Model Not Available**")
        st.error("Please configure your GEMINI_API_KEY to use AI-generated plans.")
        st.error("This app requires AI features to function properly.")
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
        prompt += "\n\nIMPORTANT: Make the output detailed, specific, and actionable. Use Markdown formatting with headers, bullet points, and proper structure. Provide comprehensive information without limiting word count."
        
        with st.spinner("🧠 AI Coach is creating your personalized plan..."):
            # Generate content
            response = model.generate_content(prompt)
            
            if not response or not response.text:
                st.error("❌ **AI Generation Failed**")
                st.error("The AI did not return any content. Please try again.")
                return
            
            # Store the generated plan
            st.session_state.generated_plan = response.text
            st.session_state.plan_type = plan_type
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
            simple_prompt = f"Create a detailed {plan_type} plan for a {profile.get('sport', 'athlete')}. Provide comprehensive information with tables and detailed explanations."
            response = model.generate_content(simple_prompt)
            st.session_state.generated_plan = response.text
            st.session_state.plan_type = plan_type
            st.session_state.workouts_generated += 1
            st.success("✅ Plan generated with fallback method!")
            st.rerun()
        except:
            st.error("❌ **Could not generate plan**")
            st.error("Please check your API key and try again.")

# ---------------- PAGE FUNCTIONS ----------------

def dashboard_page():
    st.markdown('<div class="main-header"><h1>🏠 Welcome to CoachBot AI!</h1></div>', unsafe_allow_html=True)
    
    # AI Status Check
    st.subheader("🤖 AI System Status")
    if model:
        st.success("✅ **AI Model Connected and Ready**")
        st.info("All features are powered by AI. Your plans and advice will be personalized based on your profile.")
    else:
        st.error("❌ **AI Model Not Connected**")
        st.error("The app requires a valid GEMINI_API_KEY to function.")
        st.warning("Please add your API key to Streamlit secrets to enable all features.")
    
    st.markdown("---")
    
    # Quick Stats
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("📊 AI Plans Generated", st.session_state.workouts_generated)
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
        - 📥 Download your plans as PDF
        
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
        6. Download PDF plans
        """)
    
    st.markdown("---")
    
    # Features Overview
    st.subheader("✨ AI-Powered Features")
    features = {
        "AI Workout Plans": "Personalized training plans generated by AI based on your profile",
        "AI Nutrition Plans": "Custom meal plans and nutrition advice from AI",
        "AI Recovery Plans": "AI-driven injury prevention and recovery strategies",
        "AI Mental Training": "AI-powered sports psychology and motivation techniques",
        "AI Tactical Tips": "AI-generated sport-specific strategies and game intelligence",
        "24/7 AI Coach Chat": "Real-time AI coaching and personalized advice",
        "PDF Download": "Download your generated plans as professional PDF documents"
    }
    
    for feature, description in features.items():
        st.markdown(f"""
        <div class="metric-card">
            <h3>🤖 {feature}</h3>
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

def training_plan_page():
    try:
        st.markdown('<div class="main-header"><h1>💪 AI Training Plan Generator</h1></div>', unsafe_allow_html=True)
        
        # Check if API is available
        if not model:
            st.error("❌ **AI Features Not Available**")
            st.error("This app requires a valid Google Generative AI API key.")
            st.error("Please configure your GEMINI_API_KEY in Streamlit secrets.")
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
            
            # Download PDF button
            col1, col2, col3 = st.columns([1, 1, 1])
            with col2:
                plan_type = st.session_state.get('plan_type', 'Workout Plan')
                if st.button("📥 Download Plan as PDF", use_container_width=True):
                    try:
                        pdf_buffer = create_pdf(st.session_state.generated_plan, plan_type)
                        st.download_button(
                            label="⬇️ Click to Download PDF",
                            data=pdf_buffer,
                            file_name=f"CoachBot_{plan_type.replace(' ', '_')}_Plan.pdf",
                            mime="application/pdf"
                        )
                    except Exception as e:
                        st.error(f"❌ **PDF Generation Error:** {str(e)}")
                        st.info("An error occurred while creating the PDF. Please try again.")
            
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
        st.error("Please configure your GEMINI_API_KEY in Streamlit secrets.")
        st.info("""
        **To enable AI features:**
        1. Get your API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
        2. Add it to Streamlit secrets as `GEMINI_API_KEY`
        3. Restart the app
        
        **This app requires AI features to work properly.**
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
                    <div style="background: #667eea; color: white; padding: 15px; border-radius: 10px; margin: 10px 0;">
                        <strong>You:</strong> {message['content']}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.markdown(f"""
                    <div style="background: white; padding: 15px; border-radius: 10px; margin: 10px 0; border-left: 4px solid #667eea;">
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

