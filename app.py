import streamlit as st
import time
import controller

st.title("Dungeons and Dragons Character Creator")
st.write("WARNING: Do NOT put any personal information into the Character Creator.")

# Add a simple interactive widget
character_prompt = st.text_input("Enter a description of the character you would like to create:")
if character_prompt:
    with st.spinner(text="In progress...", show_time=False, width="content"):
        try:
            file_name = controller.main(character_prompt)
        except Exception as e:
            st.write("There was an issue creating your character, please try again")
    if file_name:      
        st.success("Done!")
        with open(file=file_name,mode="r",encoding='utf-8',errors='ignore') as file:
            st.download_button(label="Download Character Sheet", data=file, file_name=file_name)
