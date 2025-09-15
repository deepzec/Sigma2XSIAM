import sys
import os

# Add the project directory to Python path to find the custom backend
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Import from installed pySigma packages
from sigma.rule import SigmaRule
from sigma.processing.pipeline import ProcessingPipeline

# Import your standalone custom backend (no dependencies on sigma.backends.base)
try:
    from cortex.backends.cortexxsiam import CortexXSIAMBackend
    print("✅ Custom CortexXSIAMBackend imported successfully")
except ImportError as e:
    print(f"❌ Failed to import custom backend: {e}")
    print("Make sure the file exists at: cortex/backends/cortexxsiam.py")
    print("And that cortex/__init__.py and cortex/backends/__init__.py exist")
    exit(1)
from sigma.processing.resolver import ProcessingPipelineResolver
import yaml
import os

print("--- Starting Sigma to XSIAM Conversion ---")

try:
    # Check if files exist
    pipeline_file = "pipelines/cortex_xdm.yml"
    rule_file = "rule.yml"
    
    if not os.path.exists(pipeline_file):
        print(f"❌ Pipeline file not found: {pipeline_file}")
        exit(1)
    
    if not os.path.exists(rule_file):
        print(f"❌ Rule file not found: {rule_file}")
        exit(1)
    
    # Load the custom processing pipeline
    print("Loading YAML pipeline...")
    with open(pipeline_file, "r", encoding='utf-8') as f:
        pipeline_yaml = f.read()
    
    # Try different methods to load pipeline
    try:
        pipeline = ProcessingPipeline.from_yaml(pipeline_yaml)
    except AttributeError:
        # Alternative method for newer versions
        pipeline_data = yaml.safe_load(pipeline_yaml)
        pipeline = ProcessingPipeline(pipeline_data)
    
    print("Pipeline loaded successfully.")
    
    # Initialize the backend with the pipeline
    print("Initializing backend...")
    siem_backend = CortexXSIAMBackend(processing_pipeline=pipeline)
    print("Backend initialized successfully.")
    
    # Load the Sigma rule
    print("Loading Sigma rule...")
    with open(rule_file, "r", encoding='utf-8') as f:
        rule_yaml = f.read()
    
    
    sigma_rule = SigmaRule.from_yaml(rule_yaml)
    print("Rule loaded successfully.")
    
    
    
    
    # Convert the rule
    print("Converting rule...")
    conversion_result = siem_backend.convert_rule(sigma_rule)
    
    # Handle different return types
    if isinstance(conversion_result, list):
        xql_query = conversion_result[0]
    else:
        xql_query = conversion_result
    
    print("\n✅--- CONVERSION SUCCESSFUL ---✅")
    print("Generated XSIAM Query:")
    print(xql_query)
    
except ImportError as e:
    print(f"\n❌--- IMPORT ERROR ---❌")
    print(f"Import failed: {e}")
    print("\nTry installing required packages:")
    print("pip install pysigma pysigma-backend-cortexxsiam")
    
except FileNotFoundError as e:
    print(f"\n❌--- FILE NOT FOUND ---❌")
    print(f"File error: {e}")
    
except yaml.YAMLError as e:
    print(f"\n❌--- YAML PARSING ERROR ---❌")
    print(f"YAML error: {e}")
    
except Exception as e:
    print(f"\n❌--- CONVERSION FAILED ---❌")
    print(f"An error occurred: {e}")
    print(f"Error type: {type(e).__name__}")
    
    # Additional debugging info
    try:
        import sigma
        print(f"Sigma version: {sigma.__version__}")
    except:
        print("Could not determine Sigma version")
