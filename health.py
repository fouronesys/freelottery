import streamlit as st

# Endpoint mínimo solo para CapRover
def health_check():
    return "ok"

# Puedes mostrarlo como un botón o un text oculto
if st.button("Health"):
    st.write(health_check())
