from fastapi import APIRouter, UploadFile, File, HTTPException
from services.price_processor import PriceProcessor
import tempfile
import os

router = APIRouter()
price_processor = PriceProcessor()

@router.post("/process")
async def process_price_list(file: UploadFile = File(...)):
    # Validate file extension
    if not file.filename.endswith(('.csv', '.xls', '.xlsx')):
        raise HTTPException(
            status_code=400,
            detail="Invalid file format. Only CSV and Excel files are supported."
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
    
    try:
        # Process the file
        result = await price_processor.process_price_list(temp_path)
        
        if not result["success"]:
            raise HTTPException(status_code=400, detail=result["error"])
        
        return result
    finally:
        # Clean up temporary file
        os.unlink(temp_path) 