from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, Form
from services.price_processor import PriceProcessor
from core.config import get_vector_db_client
import tempfile
import os
import logging
import traceback

router = APIRouter()
logger = logging.getLogger(__name__)

async def get_qdrant_client():
    """Get Qdrant client instance using centralized configuration"""
    return get_vector_db_client()

async def get_price_processor():
    """Get price processor instance"""
    return PriceProcessor()

@router.post("/process")
async def process_price_list(
    file: UploadFile = File(...),
    supplier_id: str = Form(...),
    price_processor: PriceProcessor = Depends(get_price_processor)
):
    """
    Process a price list file (CSV or Excel) and store it in supplier-specific collection.
    Each supplier maintains their latest 3 price lists.
    
    The file should contain the following columns:
    - name: Material name
    - category: Material category
    - unit: Unit of measurement
    - price: Price value
    - description: (optional) Material description
    
    Parameters:
    - file: CSV or Excel file with price list
    - supplier_id: Unique identifier of the supplier
    """
    logger.info(f"Received file: {file.filename}, content_type: {file.content_type}")
    
    # Validate file extension
    if not file.filename.lower().endswith(('.csv', '.xls', '.xlsx')):
        logger.error(f"Invalid file format: {file.filename}")
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file format: {file.filename}. Only CSV and Excel files are supported."
        )
    
    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        content = await file.read()
        temp_file.write(content)
        temp_path = temp_file.name
        logger.info(f"Saved file to: {temp_path}")
    
    try:
        # Process the file
        result = await price_processor.process_price_list(temp_path, supplier_id)
        
        return {
            "message": "Price list processed successfully",
            "supplier_id": result["supplier_id"],
            "materials_processed": result["materials_processed"],
            "upload_date": result["upload_date"]
        }
    except ValueError as e:
        logger.error(f"Processing error: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Processing error: {str(e)}")
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        logger.error("Unexpected error:")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_path)
        except Exception as e:
            logger.warning(f"Could not delete temp file {temp_path}: {e}")

@router.get("/{supplier_id}/latest")
async def get_latest_price_list(
    supplier_id: str,
    price_processor: PriceProcessor = Depends(get_price_processor)
):
    """
    Get the latest price list for a specific supplier.
    
    Parameters:
    - supplier_id: Unique identifier of the supplier
    """
    try:
        result = price_processor.get_latest_price_list(supplier_id)
        
        if result["total_count"] == 0:
            raise HTTPException(
                status_code=404, 
                detail=f"No price lists found for supplier {supplier_id}"
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting latest price list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.get("/{supplier_id}/all")
async def get_all_price_lists(
    supplier_id: str,
    price_processor: PriceProcessor = Depends(get_price_processor)
):
    """
    Get all price lists for a specific supplier (grouped by upload date).
    
    Parameters:
    - supplier_id: Unique identifier of the supplier
    """
    try:
        result = price_processor.get_all_price_lists(supplier_id)
        return result
    except Exception as e:
        logger.error(f"Error getting all price lists: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@router.delete("/{supplier_id}")
async def delete_supplier_price_list(
    supplier_id: str,
    price_processor: PriceProcessor = Depends(get_price_processor)
):
    """
    Delete all price lists for a specific supplier.
    
    Parameters:
    - supplier_id: Unique identifier of the supplier
    """
    try:
        success = price_processor.delete_supplier_prices(supplier_id)
        if success:
            return {"message": f"All price lists for supplier {supplier_id} have been deleted"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete supplier price lists")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting price list: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}") 