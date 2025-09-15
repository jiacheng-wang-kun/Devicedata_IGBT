#!/usr/bin/env python3
"""
TXT to VAMS Converter
Convert neural network weight txt files to Verilog-A model parameters (.vams) files

Author: AI Assistant
Date: 2024
Purpose: Convert trained neural network model parameters to Verilog-A format for SPICE simulators
"""

import os
import re
import argparse
from pathlib import Path


def parse_txt_file(txt_file_path):
    """
    Parse txt file and extract neural network weights and bias parameters
    
    Args:
        txt_file_path (str): Path to txt file
        
    Returns:
        dict: Dictionary containing weights and biases
    """
    weights_data = {}
    
    with open(txt_file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Split content by layers
    layers = content.split('\n\n')
    
    for layer in layers:
        if not layer.strip():
            continue
            
        lines = layer.strip().split('\n')
        if not lines:
            continue
            
        # Parse layer name
        layer_name = lines[0].rstrip(':')
        
        # Parse weight/bias data
        data_values = []
        for line in lines[1:]:
            if line.strip():
                # Split values in each line
                values = line.strip().split()
                for value in values:
                    try:
                        data_values.append(float(value))
                    except ValueError:
                        continue
        
        if data_values:
            weights_data[layer_name] = data_values
    
    return weights_data


def convert_to_vams_format(weights_data, model_name="igbt_physnet"):
    """
    Convert weight data to VAMS format
    
    Args:
        weights_data (dict): Dictionary containing weights and biases
        model_name (str): Model name
        
    Returns:
        str: VAMS format string
    """
    vams_lines = []
    
    # Add file header comments
    vams_lines.append(f"// Verilog-A Model Parameters for {model_name}")
    vams_lines.append("// Generated from neural network weights")
    vams_lines.append("// Format: variable_name = value;")
    vams_lines.append("")
    
    # Process input normalization parameters
    if 'layers.0.weight' in weights_data:
        # Assume first layer is input layer, extract input normalization parameters
        input_weights = weights_data['layers.0.weight']
        if len(input_weights) >= 3:
            vams_lines.append("// Input normalization parameters")
            vams_lines.append(f"input_mean_0 = {input_weights[0]:.10e};")
            vams_lines.append(f"input_mean_1 = {input_weights[1]:.10e};")
            vams_lines.append(f"input_mean_2 = {input_weights[2]:.10e};")
            vams_lines.append(f"input_std_0 = {input_weights[3]:.10e};")
            vams_lines.append(f"input_std_1 = {input_weights[4]:.10e};")
            vams_lines.append(f"input_std_2 = {input_weights[5]:.10e};")
            vams_lines.append("")
    
    # Process output normalization parameters
    vams_lines.append("// Output normalization parameters")
    vams_lines.append("output_mean = 0.0000000000e+00;")
    vams_lines.append("output_std = 1.0000000000e+00;")
    vams_lines.append("")
    
    # Process hidden layer weights
    layer_idx = 0
    for layer_name, data in weights_data.items():
        if 'weight' in layer_name and 'layers.0' not in layer_name:
            layer_idx += 1
            
            # Determine layer type
            if layer_idx == 1:
                layer_prefix = "h1"
            elif layer_idx == 2:
                layer_prefix = "h2"
            else:
                layer_prefix = f"h{layer_idx}"
            
            vams_lines.append(f"// {layer_prefix.upper()} layer weights")
            
            # Convert weights
            for i, weight in enumerate(data):
                vams_lines.append(f"weights_{layer_prefix}_{i} = {weight:.10e};")
            
            vams_lines.append("")
    
    # Process biases
    layer_idx = 0
    for layer_name, data in weights_data.items():
        if 'bias' in layer_name and 'layers.0' not in layer_name:
            layer_idx += 1
            
            # Determine layer type
            if layer_idx == 1:
                layer_prefix = "h1"
            elif layer_idx == 2:
                layer_prefix = "h2"
            else:
                layer_prefix = f"h{layer_idx}"
            
            vams_lines.append(f"// {layer_prefix.upper()} layer biases")
            
            # Convert biases
            for i, bias in enumerate(data):
                vams_lines.append(f"bias_{layer_prefix}_{i} = {bias:.10e};")
            
            vams_lines.append("")
    
    # Process output layer weights
    if 'layers.4.weight' in weights_data:
        vams_lines.append("// Output layer weights")
        output_weights = weights_data['layers.4.weight']
        for i, weight in enumerate(output_weights):
            vams_lines.append(f"weights_out_{i} = {weight:.10e};")
        vams_lines.append("")
    
    # Process output layer bias
    if 'layers.4.bias' in weights_data:
        vams_lines.append("// Output layer bias")
        output_bias = weights_data['layers.4.bias']
        for i, bias in enumerate(output_bias):
            vams_lines.append(f"bias_out_{i} = {bias:.10e};")
        vams_lines.append("")
    
    return '\n'.join(vams_lines)


def convert_txt_to_vams(txt_file_path, output_file_path=None, model_name=None):
    """
    Convert txt file to vams file
    
    Args:
        txt_file_path (str): Input txt file path
        output_file_path (str): Output vams file path (optional)
        model_name (str): Model name (optional)
    """
    # Check if input file exists
    if not os.path.exists(txt_file_path):
        raise FileNotFoundError(f"Input file does not exist: {txt_file_path}")
    
    # Generate output filename
    if output_file_path is None:
        txt_path = Path(txt_file_path)
        output_file_path = txt_path.parent / f"{txt_path.stem}_converted.vams"
    
    # Generate model name
    if model_name is None:
        model_name = Path(txt_file_path).stem
    
    print(f"Converting file: {txt_file_path}")
    print(f"Output file: {output_file_path}")
    print(f"Model name: {model_name}")
    
    # Parse txt file
    weights_data = parse_txt_file(txt_file_path)
    
    # Convert to VAMS format
    vams_content = convert_to_vams_format(weights_data, model_name)
    
    # Write to output file
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(vams_content)
    
    print(f"Conversion completed! Generated {len(vams_content.splitlines())} lines of VAMS code")
    
    # Display statistics
    print("\nStatistics:")
    for layer_name, data in weights_data.items():
        print(f"  {layer_name}: {len(data)} parameters")


def batch_convert(input_dir, output_dir=None, pattern="*_weights.txt"):
    """
    Batch convert all txt files in directory
    
    Args:
        input_dir (str): Input directory
        output_dir (str): Output directory (optional)
        pattern (str): File matching pattern
    """
    input_path = Path(input_dir)
    
    if output_dir is None:
        output_path = input_path
    else:
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all matching txt files
    txt_files = list(input_path.glob(pattern))
    
    if not txt_files:
        print(f"No files found matching pattern '{pattern}' in {input_dir}")
        return
    
    print(f"Found {len(txt_files)} files to convert")
    
    for txt_file in txt_files:
        try:
            output_file = output_path / f"{txt_file.stem}_converted.vams"
            convert_txt_to_vams(str(txt_file), str(output_file))
            print("-" * 50)
        except Exception as e:
            print(f"Error converting file {txt_file}: {e}")


def main():
    """Main function"""
    parser = argparse.ArgumentParser(
        description="Convert neural network weight txt files to Verilog-A model parameters (.vams) files",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage examples:
  # Convert single file
  python txt_to_vams_converter.py input.txt -o output.vams -n my_model
  
  # Batch convert all files in directory
  python txt_to_vams_converter.py -d weights_txt/ -o vams_output/
  
  # Convert files matching specific pattern
  python txt_to_vams_converter.py -d weights_txt/ -p "*_L1_weights.txt"
        """
    )
    
    parser.add_argument('input', nargs='?', help='Input txt file path')
    parser.add_argument('-o', '--output', help='Output vams file path')
    parser.add_argument('-n', '--name', help='Model name')
    parser.add_argument('-d', '--directory', help='Batch convert directory')
    parser.add_argument('-p', '--pattern', default='*_weights.txt', 
                       help='File matching pattern for batch conversion (default: *_weights.txt)')
    
    args = parser.parse_args()
    
    try:
        if args.directory:
            # Batch conversion mode
            batch_convert(args.directory, args.output, args.pattern)
        elif args.input:
            # Single file conversion mode
            convert_txt_to_vams(args.input, args.output, args.name)
        else:
            parser.print_help()
    
    except Exception as e:
        print(f"Error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
