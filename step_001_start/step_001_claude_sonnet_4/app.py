# Anthropic Claude Sonnet 4      a.d. 2025-06-04

import streamlit as st

# Inicjalizacja session state
if 'page' not in st.session_state:
    st.session_state.page = 1
if 'user_text' not in st.session_state:
    st.session_state.user_text = ""
if 'confirmed_text' not in st.session_state:
    st.session_state.confirmed_text = ""

def go_to_page(page_num):
    st.session_state.page = page_num

def main():
    st.title("Aplikacja wieloekranowa")
    
    # EKRAN 1 - Wprowadzanie tekstu
    if st.session_state.page == 1:
        st.header("Ekran 1 - Wprowadź tekst")
        
        # Pole tekstowe
        user_input = st.text_area(
            "Proszę podać tekst:",
            value=st.session_state.user_text,
            height=100,
            placeholder="Wpisz tutaj swój tekst..."
        )
        
        # Zapisanie tekstu do session state
        st.session_state.user_text = user_input
        
        # Button przejścia do następnej strony
        if st.button("Przejdź dalej", type="primary"):
            if user_input.strip():  # Sprawdzenie czy tekst nie jest pusty
                go_to_page(2)
                st.rerun()
            else:
                st.error("Proszę wprowadzić jakiś tekst przed przejściem dalej!")
    
    # EKRAN 2 - Potwierdzenie
    elif st.session_state.page == 2:
        st.header("Ekran 2 - Potwierdź wprowadzony tekst")
        
        st.subheader("Wprowadzony tekst:")
        st.info(st.session_state.user_text)
        
        st.write("Czy potwierdzasz powyższy tekst?")
        
        # Dwa buttony obok siebie
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("← Powrót do poprzedniej strony"):
                go_to_page(1)
                st.rerun()
        
        with col2:
            if st.button("Potwierdź i przejdź dalej →", type="primary"):
                st.session_state.confirmed_text = st.session_state.user_text
                go_to_page(3)
                st.rerun()
    
    # EKRAN 3 - Podsumowanie
    elif st.session_state.page == 3:
        st.header("Ekran 3 - Podsumowanie")
        
        st.subheader("Potwierdzony tekst:")
        st.success(st.session_state.confirmed_text)
        
        st.write("Tekst został pomyślnie zapisany!")
        
        # Button powrotu do pierwszej strony
        if st.button("← Powrót do pierwszej strony", type="primary"):
            # Opcjonalnie: wyczyść dane
            # st.session_state.user_text = ""
            # st.session_state.confirmed_text = ""
            go_to_page(1)
            st.rerun()

    # Dodanie informatora o aktualnej stronie (opcjonalne)
    st.sidebar.write(f"Aktualna strona: {st.session_state.page}/3")
    
    # Debug info (można usunąć w wersji produkcyjnej)
    with st.sidebar.expander("Debug Info"):
        st.write("Session State:")
        st.write(f"Page: {st.session_state.page}")
        st.write(f"User text: '{st.session_state.user_text}'")
        st.write(f"Confirmed text: '{st.session_state.confirmed_text}'")

if __name__ == "__main__":
    main()
