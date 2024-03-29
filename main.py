import docx
import hmac
import pdfplumber
import streamlit as st
from io import BytesIO
from openai import OpenAI

MAX_TEMP = 1
MAX_VALUE = 100

def check_password():
    """Returns `True` if the user had the correct password."""

    def password_entered():
        """Checks whether a password entered by the user is correct."""
        if hmac.compare_digest(st.session_state["password"], st.secrets["password"]):
            st.session_state["password_correct"] = True
            del st.session_state["password"]  # Don't store the password.
        else:
            st.session_state["password_correct"] = False

    # Return True if the password is validated.
    if st.session_state.get("password_correct", False):
        return True

    st.header("Please enter the password below:")
    st.text_input(
        "Password", type="password", on_change=password_entered, key="password")
    if "password_correct" in st.session_state:
        st.error("😕 Password incorrect")
    return False

def extract_text(file, file_type):
    text = ""
    if file_type == "application/pdf":
        with pdfplumber.open(file) as pdf:
            for page in pdf.pages:
                text += page.extract_text() + "\n"
    elif file_type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
        # Convert the uploaded file to BytesIO for docx
        doc = docx.Document(BytesIO(file.getvalue()))
        for para in doc.paragraphs:
            text += para.text + "\n"
    return text

def generate(api_key, system_prompt, prompt, creativity=80):
    response = OpenAI(api_key=api_key).chat.completions.create(
        model="gpt-4-0125-preview",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ],
        temperature=creativity/(1/MAX_TEMP*MAX_VALUE),
    )
    return response.choices[0].message.content.strip()


def main():
    st.set_page_config(layout="centered", page_title="Lit Reviaew",page_icon="📖")
    st.title("Lit Review AI 📖")
    openai_api_key = st.secrets["OPENAI_API_KEY"]
    creativity = st.slider("Creativity", min_value=0,max_value=MAX_VALUE,value=80,format="%d%%")
    word_count = st.slider("Word Count", min_value=100,max_value=2000,value=500,format="%d words")
    topic = st.text_area("Provide a brief description of the the topic:", placeholder="Enter text here...")
    example = st.text_area("Provide a an example of your writing for style purposes:", placeholder="Enter text here...")
    document = st.file_uploader(label="Document:", type=["pdf", "docx"])
    if document is not None:
        document_text = extract_text(document, document.type)



    if openai_api_key:
        if st.button("Generate"):
            try:
                with st.spinner("Generating Lit Review..."):
                    system_prompt = """Create detailed, analytical literature reviews from provided documents. Your response should synthesize key findings, critique methodologies, and identify research gaps. Employ critical thinking to evaluate the relevance and impact of each study within the broader field. Structure your review logically, starting with an overview of the topic, followed by thematic analysis, and concluding with potential avenues for future research. Ensure clarity, coherence, and adherence to academic writing standards, including appropriate citation formats."""

                    prompt = f"""
                    # TOPIC:
                    {topic}

                    # DOCUMENT TEXT:
                    "{document_text}"

                    # WORD COUNT:
                    Aim for exactly {word_count} words.
                    """
                    response = generate(openai_api_key, system_prompt.strip(), prompt.strip(), creativity)
                
                with st.spinner("Making Original..."):
                    edit_system_prompt = """Modify the provided text for enhanced originality to avoid plagiarism detection by rephrasing key points, offering fresh evaluations of methodologies, and illuminating research gaps with new perspectives. Restructure content as needed for logical flow, and enhance clarity and coherence. Prioritize maintaining the original's meaning and scholarly value while ensuring the text is sufficiently unique to avoid plagiarism detection. Use the provided text as example for writing style only, do not consider the content. Use the example text in double quotation marks below as a guide for stylistic purposes alone, disregarding its specific content."""

                    edit_prompt = f"""
                    # Text to modify:
                    {response}

                    # EXAMPLE FOR STYLE:
                    "{example}"
                    """
                    edited_reponse = generate(openai_api_key, edit_system_prompt.strip(), edit_prompt.strip(), creativity)
                    st.write(edited_reponse)
            except:
                st.warning("Error generating resopne. Please try again.")

if not check_password():
    st.stop()  # Prevent access to the app if password check fails

if __name__ == '__main__':
    main()