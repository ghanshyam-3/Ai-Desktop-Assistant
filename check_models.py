print("Starting import...")
import openwakeword
print("Imported openwakeword")
from openwakeword.model import Model
print("Imported Model")
openwakeword.utils.download_models()
print("Models downloaded/checked")
