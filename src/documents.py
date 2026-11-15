
from pathlib import Path
from pypdf import PdfReader


def extract_pdf_text(pdf_file):
    """
    Extract text from an uploaded PDF file.
    Supports Streamlit UploadedFile and local file paths.
    """

    try:
        if isinstance(pdf_file, (str, Path)):
            reader = PdfReader(str(pdf_file))
            filename = Path(pdf_file).name
        else:
            pdf_file.seek(0)
            reader = PdfReader(pdf_file)
            filename = getattr(pdf_file, "name", "uploaded_resume.pdf")

        if reader.is_encrypted:
            raise ValueError(
                "This PDF is password protected. Please upload an accessible PDF."
            )

        pages = []
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""

            if text.strip():
                pages.append(
                    f"--- Page {page_number} ---\n{text.strip()}"
                )

        extracted_text = "\n\n".join(pages).strip()

        if not extracted_text:
            raise ValueError(
                "No readable text found. This may be a scanned PDF."
            )

        return {
            "filename": filename,
            "total_pages": len(reader.pages),
            "text": extracted_text,
            "character_count": len(extracted_text)
        }

    except ValueError:
        raise

    except Exception as error:
        raise RuntimeError(
            f"Unable to process PDF: {error}"
        ) from error


def validate_resume_text(text):
    """Validate extracted resume content."""

    if not text or not text.strip():
        raise ValueError("Resume content is empty.")

    if len(text.strip()) < 100:
        raise ValueError(
            "Resume contains too little readable text for reliable analysis."
        )

    return True


def get_resume_summary_input(resume_data):
    """Prepare extracted resume content for AI analysis."""

    validate_resume_text(resume_data["text"])

    return {
        "filename": resume_data["filename"],
        "pages": resume_data["total_pages"],
        "character_count": resume_data["character_count"],
        "resume_text": resume_data["text"]
    }
