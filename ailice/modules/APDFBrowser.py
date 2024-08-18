import os
import shutil
import requests
import subprocess
import importlib.util
from pathlib import Path

# Determine the OCR option to use based on installed packages
OCROption = "None"
if importlib.util.find_spec("marker") is not None:
    OCROption = "marker"
elif importlib.util.find_spec("pix2text") is not None:
    from pix2text import Pix2Text
    OCROption = "pix2text"

from ailice.modules.AScrollablePage import AScrollablePage

class APDFBrowser(AScrollablePage):
    def __init__(self, pdfOutputDir: str, functions: dict[str, str]):
        super().__init__(functions=functions)
        self.pdfOutputDir = pdfOutputDir
        if OCROption == "pix2text":
            self.p2t = Pix2Text.from_config()

    def OCRPix2Text(self, pdfPath: str, outDir: str) -> str:
        return self.p2t.recognize_pdf(pdfPath).to_markdown(outDir)

    def OCRMarker(self, pdfPath: str, outDir: str) -> str:
        subprocess.run(["marker_single", pdfPath, outDir, "--batch_multiplier", "2"], check=True)
        pdfName = Path(pdfPath).stem
        result_file = Path(outDir) / pdfName / f"{pdfName}.md"
        with open(result_file, "r") as f:
            return f.read()
    
    def Browse(self, url: str) -> str:
        if OCROption == "None":
            self.LoadPage("Python packages 'marker' or 'pix2text' not found. Please install one of them before using PDF OCR.", "BOTTOM")
            return self()
        
        try:
            fullName = url.split('/')[-1]
            fileName = fullName.rsplit('.', 1)[0]
            outDir = Path(self.pdfOutputDir) / fileName
            outDir.mkdir(parents=True, exist_ok=True)
            
            pdfPath = outDir / fullName
            if Path(url).exists():
                shutil.copy(url, pdfPath)
            else:
                response = requests.get(url)
                if response.status_code == 200:
                    with open(pdfPath, "wb") as pdf_file:
                        pdf_file.write(response.content)
                else:
                    print(f"Cannot download PDF file. HTTP error code: {response.status_code}")
                    return self()
            
            if OCROption == "marker":
                result = self.OCRMarker(pdfPath, outDir)
            elif OCROption == "pix2text":
                result = self.OCRPix2Text(pdfPath, outDir)
            self.LoadPage(result, "TOP")
        except Exception as e:
            self.LoadPage(f"PDF OCR Exception: {str(e)}.", "BOTTOM")
        return self()
    
    def GetFullText(self) -> str:
        return self.txt if self.txt is not None else ""
