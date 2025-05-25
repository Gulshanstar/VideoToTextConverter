import streamlit as st
import google.generativeai as genai
import requests
import tempfile
import os
from pathlib import Path
import time

# Page configuration
st.set_page_config(
    page_title="Video Text Extractor",
    page_icon="🎥",
    layout="wide"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        text-align: center;
        padding: 1rem 0;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .result-box {
        background-color: ##000000;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #007bff;
        margin: 1rem 0;
    }
    .summary-box {
        background-color: ##000000;
        padding: 1rem;
        border-radius: 8px;
        border-left: 4px solid #28a745;
        margin: 1rem 0;
    }
    .stProgress > div > div > div > div {
        background-color: #667eea;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown("""
<div class="main-header">
    <h1>🎥 Video Text Extractor & Summarizer</h1>
    <p>Extract text and speech from videos using Google Gemini AI</p>
</div>
""", unsafe_allow_html=True)

class StreamlitVideoExtractor:
    def __init__(self, api_key):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def download_video(self, video_url):
        """Download video from URL"""
        try:
            with st.spinner("📥 Downloading video..."):
                response = requests.get(video_url, stream=True)
                response.raise_for_status()
                
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                
                # Progress bar for download
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                if total_size > 0:
                    progress_bar = st.progress(0)
                    
                for chunk in response.iter_content(chunk_size=8192):
                    temp_file.write(chunk)
                    if total_size > 0:
                        downloaded += len(chunk)
                        progress_bar.progress(downloaded / total_size)
                
                temp_file.close()
                st.success("✅ Video downloaded successfully!")
                return temp_file.name
                
        except Exception as e:
            st.error(f"❌ Error downloading video: {str(e)}")
            return None
    
    def upload_video_to_gemini(self, video_path):
        """Upload video to Gemini and wait for processing"""
        try:
            with st.spinner("☁️ Uploading video to Gemini..."):
                video_file = genai.upload_file(path=video_path)
                st.success("✅ Video uploaded to Gemini!")
                
                # Wait for file to be processed
                st.info("⏳ Waiting for video to be processed by Gemini (this may take a few minutes)...")
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                max_wait_time = 300  # 5 minutes max wait
                wait_time = 0
                
                while video_file.state.name == "PROCESSING":
                    wait_time += 2
                    progress = min(wait_time / max_wait_time, 0.9)  # Don't go to 100% until done
                    progress_bar.progress(progress)
                    
                    status_text.text(f"Processing... ({wait_time}s) - Status: {video_file.state.name}")
                    
                    if wait_time > max_wait_time:
                        st.error("⏰ Processing timeout. Please try with a shorter video.")
                        return None
                    
                    time.sleep(2)
                    video_file = genai.get_file(video_file.name)
                
                progress_bar.progress(1.0)
                status_text.empty()
                
                if video_file.state.name == "FAILED":
                    st.error("❌ Video processing failed! Please try with a different video.")
                    return None
                elif video_file.state.name == "ACTIVE":
                    st.success("✅ Video is ready for analysis!")
                    return video_file
                else:
                    st.warning(f"⚠️ Unexpected file state: {video_file.state.name}")
                    return None
                    
        except Exception as e:
            st.error(f"❌ Error uploading video: {str(e)}")
            return None
    
    def extract_text_from_video(self, video_file):
        """Extract text from video"""
        try:
            with st.spinner("🔍 Extracting text from video..."):
                prompt = """
                Please extract ALL text content from this video including:
                1. All spoken dialogue and narration (transcribe speech to text)
                2. Any text that appears on screen (titles, captions, signs, etc.)
                3. Any other textual information visible in the video
                
                Provide the complete transcript in chronological order.
                If there are multiple speakers, indicate speaker changes.
                """
                
                response = self.model.generate_content([video_file, prompt])
                st.success("✅ Text extraction completed!")
                return response.text
                
        except Exception as e:
            st.error(f"❌ Error extracting text: {str(e)}")
            return None
    
    def summarize_text(self, extracted_text):
        """Create summary"""
        try:
            with st.spinner("📝 Creating summary..."):
                prompt = f"""
                Please create a comprehensive summary of the following text extracted from a video:

                {extracted_text}

                Provide:
                1. A brief overview (2-3 sentences)
                2. Key points and main topics discussed
                3. Important details or conclusions
                4. Any notable quotes or statements

                Make the summary clear, concise, and well-organized.
                """
                
                response = self.model.generate_content(prompt)
                st.success("✅ Summary created!")
                return response.text
                
        except Exception as e:
            st.error(f"❌ Error creating summary: {str(e)}")
            return None

def main():
    # Sidebar for configuration
    st.sidebar.header("🔧 Configuration")
    
    # API Key input
    api_key = st.sidebar.text_input(
        "Enter your Gemini API Key:",
        type="password",
        help="Get your free API key from Google AI Studio"
    )
    
    if not api_key:
        st.warning("⚠️ Please enter your Google Gemini API key in the sidebar to get started.")
        st.info("💡 Get your free API key from [Google AI Studio](https://aistudio.google.com/)")
        return
    
    # Initialize extractor
    extractor = StreamlitVideoExtractor(api_key)
    
    # Main interface
    st.header("📤 Upload or Provide Video")
    
    # Tab selection
    tab1, tab2 = st.tabs(["🔗 Video URL", "📁 Upload File"])
    
    video_path = None
    
    with tab1:
        st.subheader("Enter Video URL")
        video_url = st.text_input(
            "Video URL:",
            placeholder="https://example.com/video.mp4",
            help="Paste the direct link to your video file"
        )
        
        if st.button("🚀 Process Video from URL", type="primary"):
            if video_url:
                video_path = extractor.download_video(video_url)
            else:
                st.error("Please enter a video URL")
    
    with tab2:
        st.subheader("Upload Video File")
        uploaded_file = st.file_uploader(
            "Choose a video file",
            type=['mp4', 'mov', 'avi', 'webm', 'mpg', 'mpeg', 'wmv', 'flv'],
            help="Select a video file from your computer"
        )
        
        if st.button("🚀 Process Uploaded Video", type="primary"):
            if uploaded_file is not None:
                # Save uploaded file temporarily
                with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
                    tmp_file.write(uploaded_file.getvalue())
                    video_path = tmp_file.name
                    st.success("✅ File uploaded successfully!")
            else:
                st.error("Please upload a video file")
    
    # Process video if path is available
    if video_path:
        st.header("🔄 Processing")
        
        # Create progress tracker
        progress_container = st.container()
        
        with progress_container:
            # Upload to Gemini
            video_file = extractor.upload_video_to_gemini(video_path)
            
            if video_file:
                # Extract text
                extracted_text = extractor.extract_text_from_video(video_file)
                
                if extracted_text:
                    # Create summary
                    summary = extractor.summarize_text(extracted_text)
                    
                    if summary:
                        # Display results
                        st.header("📊 Results")
                        
                        # Create two columns for results
                        col1, col2 = st.columns([1, 1])
                        
                        with col1:
                            st.subheader("📝 Extracted Text")
                            st.markdown(f"""
                            <div class="result-box">
                                {extracted_text.replace('\n', '<br>')}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Download button for extracted text
                            st.download_button(
                                label="📥 Download Extracted Text",
                                data=extracted_text,
                                file_name="extracted_text.txt",
                                mime="text/plain"
                            )
                        
                        with col2:
                            st.subheader("📋 Summary")
                            st.markdown(f"""
                            <div class="summary-box">
                                {summary.replace('\n', '<br>')}
                            </div>
                            """, unsafe_allow_html=True)
                            
                            # Download button for summary
                            st.download_button(
                                label="📥 Download Summary",
                                data=summary,
                                file_name="video_summary.txt",
                                mime="text/plain"
                            )
                        
                        # Combined download
                        combined_text = f"EXTRACTED TEXT:\n{'-'*50}\n{extracted_text}\n\n\nSUMMARY:\n{'-'*50}\n{summary}"
                        st.download_button(
                            label="📥 Download Complete Report",
                            data=combined_text,
                            file_name="video_analysis_report.txt",
                            mime="text/plain"
                        )
        
        # Cleanup
        try:
            if os.path.exists(video_path):
                os.unlink(video_path)
        except:
            pass
    
    # Sidebar information
    st.sidebar.markdown("---")
    st.sidebar.header("ℹ️ Information")
    st.sidebar.info("""
    **Features:**
    - Extract speech and text from videos
    - Generate intelligent summaries
    - Support multiple video formats
    - Download results as text files
    
    **Supported Formats:**
    MP4, MOV, AVI, WEBM, MPG, MPEG, WMV, FLV
    
    **Limitations:**
    - Max file size: 2GB
    - Free tier: 15 requests/minute
    """)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("**Made with ❤️ using Streamlit & Google Gemini**")

if __name__ == "__main__":
    main()