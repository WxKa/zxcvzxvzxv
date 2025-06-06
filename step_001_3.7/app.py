# Anthropic Claude 3.7. Sonnet    a.d. 2025.06.06

import streamlit as st

# Initialize session state to store data between screens
if 'screen' not in st.session_state:
    st.session_state.screen = 1
    
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""

# Functions to navigate between screens
def go_to_screen_2():
    if st.session_state.user_input:  # Only proceed if text was entered
        st.session_state.user_text = st.session_state.user_input
        st.session_state.screen = 2
        
def go_to_screen_3():
    st.session_state.screen = 3
    
def go_back_to_screen_1():
    st.session_state.screen = 1
    
def go_back_to_screen_2():
    st.session_state.screen = 2

# App title
st.title("Three-Screen Application")

# Screen 1: Text input
if st.session_state.screen == 1:
    st.header("Screen 1")
    st.text_input("Please enter your text:", key="user_input", value=st.session_state.user_text)
    st.button("Confirm and Continue", on_click=go_to_screen_2)

# Screen 2: Confirmation
elif st.session_state.screen == 2:
    st.header("Screen 2")
    st.write("You entered:")
    st.write(st.session_state.user_text)
    
    col1, col2 = st.columns(2)
    with col1:
        st.button("Go Back", on_click=go_back_to_screen_1)
    with col2:
        st.button("Confirm and Continue", on_click=go_to_screen_3)

# Screen 3: Final screen
elif st.session_state.screen == 3:
    st.header("Screen 3")
    st.write("Confirmed text:")
    st.write(st.session_state.user_text)
    
    st.button("Return to Start", on_click=go_back_to_screen_1)