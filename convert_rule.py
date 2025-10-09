import sys
import os
import argparse
import glob

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

# Parse command-line arguments
parser = argparse.ArgumentParser(description='Convert Sigma rules to Cortex XSIAM XQL queries')
parser.add_argument('-o', '--output', type=str, help='Output file path (for single rule) or directory (for batch mode)')
parser.add_argument('-r', '--rule', type=str, help='Input Sigma rule file')
parser.add_argument('-d', '--directory', type=str, help='Directory containing Sigma rules for batch conversion')
args = parser.parse_args()

# Validate arguments
if not args.rule and not args.directory:
    # Default to rule.yml if it exists
    if os.path.exists('rule.yml'):
        args.rule = 'rule.yml'
    else:
        print("❌ Error: Please specify either -r (single rule file) or -d (directory)")
        parser.print_help()
        exit(1)

if args.rule and args.directory:
    print("❌ Error: Cannot use both -r and -d options together")
    exit(1)

def convert_single_rule(siem_backend, rule_file, output_file=None):
    """Convert a single Sigma rule to XQL"""
    try:
        # Load the Sigma rule
        with open(rule_file, "r", encoding='utf-8') as f:
            rule_yaml = f.read()
        
        sigma_rule = SigmaRule.from_yaml(rule_yaml)
        
        # Convert the rule
        conversion_result = siem_backend.convert_rule(sigma_rule)
        
        # Handle different return types
        if isinstance(conversion_result, list):
            xql_query = conversion_result[0]
        else:
            xql_query = conversion_result
        
        # Write to output file if specified
        if output_file:
            try:
                # Create directory only if there's a directory path
                dir_path = os.path.dirname(output_file)
                if dir_path:
                    os.makedirs(dir_path, exist_ok=True)
                with open(output_file, 'w', encoding='utf-8') as f:
                    f.write(xql_query)
            except Exception as e:
                print(f"⚠️  Warning: Could not write to {output_file}: {e}")
        
        return xql_query, None
        
    except Exception as e:
        return None, str(e)

print("--- Starting Sigma to XSIAM Conversion ---")

try:
    # Check if pipeline exists
    pipeline_file = "pipelines/cortex_xdm.yml"
    
    if not os.path.exists(pipeline_file):
        print(f"❌ Pipeline file not found: {pipeline_file}")
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
    print("Backend initialized successfully.\n")
    
    # Single file mode
    if args.rule:
        rule_file = args.rule
        
        if not os.path.exists(rule_file):
            print(f"❌ Rule file not found: {rule_file}")
            exit(1)
        
        print(f"Converting rule: {rule_file}")
        xql_query, error = convert_single_rule(siem_backend, rule_file, args.output)
        
        if error:
            print(f"\n❌--- CONVERSION FAILED ---❌")
            print(f"Error: {error}")
            exit(1)
        else:
            print("\n✅--- CONVERSION SUCCESSFUL ---✅")
            print("Generated XSIAM Query:")
            print(xql_query)
            
            if args.output:
                print(f"\n✅ Query saved to: {args.output}")
    
    # Directory batch mode
    elif args.directory:
        rule_dir = args.directory
        
        if not os.path.isdir(rule_dir):
            print(f"❌ Directory not found: {rule_dir}")
            exit(1)
        
        # Find all .yml and .yaml files
        rule_files = glob.glob(os.path.join(rule_dir, "**/*.yml"), recursive=True)
        rule_files.extend(glob.glob(os.path.join(rule_dir, "**/*.yaml"), recursive=True))
        
        if not rule_files:
            print(f"❌ No Sigma rule files (.yml or .yaml) found in: {rule_dir}")
            exit(1)
        
        print(f"Found {len(rule_files)} rule file(s) in {rule_dir}\n")
        
        success_count = 0
        failed_count = 0
        failed_rules = []
        
        for rule_file in rule_files:
            relative_path = os.path.relpath(rule_file, rule_dir)
            print(f"Converting: {relative_path}...", end=" ")
            
            # Determine output file path if output directory specified
            output_file = None
            if args.output:
                # Create matching directory structure in output
                output_file = os.path.join(args.output, relative_path.replace('.yml', '.xql').replace('.yaml', '.xql'))
            
            xql_query, error = convert_single_rule(siem_backend, rule_file, output_file)
            
            if error:
                print(f"❌ FAILED")
                failed_count += 1
                failed_rules.append((relative_path, error))
            else:
                print(f"✅ SUCCESS")
                success_count += 1
        
        # Print summary
        print(f"\n{'='*60}")
        print(f"CONVERSION SUMMARY")
        print(f"{'='*60}")
        print(f"Total rules processed: {len(rule_files)}")
        print(f"✅ Successful: {success_count} ({success_count/len(rule_files)*100:.2f}%)")
        print(f"❌ Failed: {failed_count} ({failed_count/len(rule_files)*100:.2f}%)")
        
        if args.output:
            print(f"\n📁 Output directory: {args.output}")
        
        if failed_rules and failed_count <= 10:
            print(f"\nFailed conversions:")
            for rule, error in failed_rules:
                print(f"  ❌ {rule}: {error}")
        elif failed_count > 10:
            print(f"\n⚠️  {failed_count} rules failed. Run individual conversions for details.")
    
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
