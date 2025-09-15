# Neural Network Model Deployment for SPICE Simulation

## Overview

This repository contains tools and procedures for deploying trained neural network models as Verilog-A behavioral models for SPICE circuit simulation. The deployment process converts PyTorch model parameters into Verilog-A model parameters (.vams files) and generates Open Source Device Interface (.osdi) files for integration with SPICE simulators.

## Architecture

The deployment pipeline consists of the following components:

1. **Trained Neural Network Model** - PyTorch model with learned parameters
2. **Weight Extraction** - Export model weights to text format
3. **VAMS Conversion** - Convert weights to Verilog-A model parameters
4. **Verilog-A Compilation** - Compile Verilog-A model using OpenVAF
5. **OSDI Generation** - Create Open Source Device Interface file
6. **SPICE Integration** - Deploy model in SPICE simulation environment

## File Structure

```
├── weights_txt/                    # Neural network weight files (.txt)
│   ├── AIKB20N60CT_L1_weights.txt
│   ├── AIKP20N60CT_L1_weights.txt
│   └── ...
├── VA-code/                       # Verilog-A model files
│   ├── igbt_physnet.va           # Main Verilog-A model
│   ├── igbt_physnet.osdi         # Open Source Device Interface
│   ├── veriloga_assign_code.vams # Model parameters
│   └── igbt_physnet_test.sp      # Test circuit
├── txt_to_vams_converter.py      # Conversion script
└── README_Deployment.md          # This file
```

## Deployment Process

### Step 1: Model Weight Extraction

The neural network model weights are exported from PyTorch to text format with the following structure:

```
layers.0.weight:
3.31696361e-01 -5.67613244e-01 7.97264636e-01
5.69172144e-01 -8.09445798e-01 -5.80563486e-01
...

layers.0.bias:
8.77201200e-01
4.81547834e-03
...

layers.2.weight:
-3.46118212e-01 2.05338612e-01 5.59260882e-02 ...
...

layers.2.bias:
-1.39581835e+00
-8.27486992e-01
...

layers.4.weight:
3.84726673e-01 7.16585517e-02 -5.72549663e-02 ...
...

layers.4.bias:
-1.13312435e+00
```

### Step 2: VAMS Parameter Generation

Use the provided Python script to convert weight files to Verilog-A model parameters:

```bash
# Convert single file
python txt_to_vams_converter.py weights_txt/AIKB20N60CT_L1_weights.txt -o VA-code/veriloga_assign_code.vams -n igbt_physnet

# Batch convert all files
python txt_to_vams_converter.py -d weights_txt/ -o VA-code/
```

The converter generates VAMS files with the following format:

```verilog
// Verilog-A Model Parameters for igbt_physnet
// Generated from neural network weights
// Format: variable_name = value;

// Input normalization parameters
input_mean_0 = 1.374074074e+01;
input_mean_1 = 1.505e+01;
input_mean_2 = 8.981481481e+01;
input_std_0 = 3.90244551e+00;
input_std_1 = 8.66020593e+00;
input_std_2 = 6.245711835e+01;

// Output normalization parameters
output_mean = 0.0000000000e+00;
output_std = 1.0000000000e+00;

// H1 layer weights
weights_h1_0 = -4.1958562000e-01;
weights_h1_1 = -6.3365871000e-01;
...

// H1 layer biases
bias_h1_0 = -3.4871575000e-01;
bias_h1_1 = -1.2070360000e-02;
...

// H2 layer weights
weights_h2_0 = -5.0243920000e-01;
weights_h2_1 = -3.8000491000e-01;
...

// H2 layer biases
bias_h2_0 = 1.2582143000e-01;
bias_h2_1 = -4.2079756000e-01;
...

// Output layer weights
weights_out_0 = 1.5226000000e-03;
weights_out_1 = 1.1593727000e-01;
...

// Output layer bias
bias_out_0 = -1.2194843000e-01;
```

### Step 3: Verilog-A Model Integration

The generated VAMS parameters are integrated into the main Verilog-A model file (`igbt_physnet.va`). The model implements the neural network forward pass using Verilog-A behavioral modeling constructs:

```verilog
// Include parameter file
`include "veriloga_assign_code.vams"

// Neural network implementation
module igbt_physnet (collector, emitter, gate, substrate);
    // Port declarations
    inout collector, emitter, gate, substrate;
    electrical collector, emitter, gate, substrate;
    
    // Internal variables for neural network computation
    real input_normalized[0:2];
    real hidden1[0:95];
    real hidden2[0:199];
    real output_value;
    
    // Neural network forward pass
    analog begin
        // Input normalization
        input_normalized[0] = (V(collector, emitter) - input_mean_0) / input_std_0;
        input_normalized[1] = (V(gate, emitter) - input_mean_1) / input_std_1;
        input_normalized[2] = (V(collector, gate) - input_mean_2) / input_std_2;
        
        // Hidden layer 1 computation
        for (i = 0; i < 96; i = i + 1) begin
            hidden1[i] = bias_h1[i];
            for (j = 0; j < 3; j = j + 1) begin
                hidden1[i] = hidden1[i] + input_normalized[j] * weights_h1[i*3 + j];
            end
            hidden1[i] = tanh(hidden1[i]); // Activation function
        end
        
        // Hidden layer 2 computation
        for (i = 0; i < 200; i = i + 1) begin
            hidden2[i] = bias_h2[i];
            for (j = 0; j < 96; j = j + 1) begin
                hidden2[i] = hidden2[i] + hidden1[j] * weights_h2[i*96 + j];
            end
            hidden2[i] = tanh(hidden2[i]); // Activation function
        end
        
        // Output layer computation
        output_value = bias_out[0];
        for (i = 0; i < 200; i = i + 1) begin
            output_value = output_value + hidden2[i] * weights_out[i];
        end
        
        // Apply output to device terminals
        I(collector, emitter) <+ output_value;
    end
endmodule
```

### Step 4: Verilog-A Compilation with OpenVAF

Compile the Verilog-A model using OpenVAF to generate the compiled model and OSDI file:

```bash
# Compile the main Verilog-A model
openvaf igbt_physnet.va

# Generate OSDI file for SPICE integration
openvaf --osdi igbt_physnet.osdi igbt_physnet.va
```

### Step 5: OSDI File Generation

The Open Source Device Interface (.osdi) file provides the interface between the Verilog-A model and SPICE simulators:

```verilog
// igbt_physnet.osdi
// Open Source Device Interface for IGBT Physical Neural Network Model

module igbt_physnet (collector, emitter, gate, substrate);
    inout collector, emitter, gate, substrate;
    electrical collector, emitter, gate, substrate;
    
    // Model parameters
    parameter real model_version = 1.0;
    parameter string model_type = "IGBT_PhysNet";
    
    // Neural network parameters
    parameter real input_mean_0 = 1.374074074e+01;
    parameter real input_mean_1 = 1.505e+01;
    parameter real input_mean_2 = 8.981481481e+01;
    parameter real input_std_0 = 3.90244551e+00;
    parameter real input_std_1 = 8.66020593e+00;
    parameter real input_std_2 = 6.245711835e+01;
    
    // Include the main Verilog-A model
    `include "igbt_physnet.va"
endmodule
```

### Step 6: SPICE Integration

The model can be used in SPICE simulations by including the OSDI file:

```spice
* IGBT Physical Neural Network Test Circuit
.include "igbt_physnet.osdi"

* Test circuit
X1 collector emitter gate substrate igbt_physnet

* Voltage sources
Vcc collector 0 600V
Vge gate emitter 0V
Vsub substrate 0 0V

* Analysis
.dc Vge 0 15 0.1
.probe I(X1.collector)
.end
```

## Usage Instructions

### Prerequisites

- Python 3.6 or higher
- SPICE simulator with Verilog-A support (e.g., ngspice, Spectre, HSPICE)
- OpenVAF (Open Verilog-A Frontend) - for Verilog-A compilation
- Verilog-A compiler (optional, if not using OpenVAF)

### Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd Devicedata_IGBT
```

2. Install Python dependencies:
```bash
pip install numpy torch
```

3. Install OpenVAF:
```bash
# Download OpenVAF from https://github.com/OpenVAF/OpenVAF
# Or install via package manager (if available)
# Follow OpenVAF installation instructions for your platform
```

### Converting Model Weights

1. **Single file conversion:**
```bash
python txt_to_vams_converter.py weights_txt/AIKB20N60CT_L1_weights.txt -o VA-code/veriloga_assign_code.vams -n igbt_physnet
```

2. **Batch conversion:**
```bash
python txt_to_vams_converter.py -d weights_txt/ -o VA-code/ -p "*_L1_weights.txt"
```

3. **Custom output directory:**
```bash
python txt_to_vams_converter.py -d weights_txt/ -o custom_output/ -n custom_model
```

### Compiling Verilog-A Models with OpenVAF

Before running SPICE simulations, compile the Verilog-A model using OpenVAF:

1. **Compile the main model:**
```bash
openvaf igbt_physnet.va
```

2. **Compile with specific options:**
```bash
openvaf -o igbt_physnet.compiled igbt_physnet.va
```

3. **Generate OSDI file:**
```bash
openvaf --osdi igbt_physnet.osdi igbt_physnet.va
```

### Running SPICE Simulations

1. **Using ngspice with OpenVAF compiled model:**
```bash
ngspice -b igbt_physnet_test.sp
```

2. **Using Spectre:**
```bash
spectre igbt_physnet_test.sp
```

3. **Using HSPICE:**
```bash
hspice igbt_physnet_test.sp
```

## Model Architecture

The neural network model implements a multi-layer perceptron with the following architecture:

- **Input Layer**: 3 inputs (collector-emitter voltage, gate-emitter voltage, collector-gate voltage)
- **Hidden Layer 1**: 96 neurons with tanh activation
- **Hidden Layer 2**: 200 neurons with tanh activation  
- **Output Layer**: 1 output (collector current)

### Input Normalization

Input voltages are normalized using learned mean and standard deviation parameters:

```
normalized_input = (raw_input - mean) / std
```

### Activation Functions

- **Hidden layers**: Hyperbolic tangent (tanh)
- **Output layer**: Linear (no activation function)

## Validation and Testing

### Model Validation

1. **Parameter verification**: Ensure all weights and biases are correctly converted
2. **Numerical accuracy**: Compare Verilog-A model outputs with PyTorch model
3. **Convergence testing**: Verify model stability in SPICE simulations

### Test Cases

The repository includes test circuits for:
- DC characteristics
- Transient response
- Temperature dependence
- Process variations

## Troubleshooting

### Common Issues

1. **Conversion errors**: Check input file format and ensure all layers are present
2. **OpenVAF compilation errors**: Verify Verilog-A syntax and check for missing dependencies
3. **Simulation convergence**: Adjust SPICE solver settings or model parameters
4. **Memory issues**: Reduce model complexity or use 64-bit SPICE simulator
5. **OSDI file issues**: Ensure OpenVAF generated OSDI file is compatible with your SPICE simulator

### Debug Mode

Enable debug output in the converter:
```bash
python txt_to_vams_converter.py input.txt -o output.vams -n model_name --debug
```

## Performance Considerations

### Computational Efficiency

- **Matrix operations**: Optimized for SPICE simulator performance
- **Memory usage**: Efficient parameter storage and access
- **Convergence**: Robust numerical implementation

### Accuracy vs. Speed Trade-offs

- **High accuracy**: Use full precision parameters
- **Fast simulation**: Reduce model complexity or use lookup tables
- **Balanced**: Default settings provide good accuracy-speed trade-off

## Contributing

### Adding New Models

1. Export model weights in the specified text format
2. Use the converter script to generate VAMS parameters
3. Update the Verilog-A model if architecture changes
4. Test thoroughly with SPICE simulations

### Code Style

- Follow Verilog-A coding standards
- Include comprehensive comments
- Use consistent naming conventions
- Document all parameters and functions

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Citation

If you use this deployment framework in your research, please cite:

```bibtex
@article{igbt_physnet_deployment,
  title={Neural Network Model Deployment for SPICE Circuit Simulation},
  author={Your Name},
  journal={IEEE Transactions on Computer-Aided Design},
  year={2024}
}
```

## Contact

For questions or support, please contact:
- Email: your.email@institution.edu
- GitHub Issues: [Repository Issues Page]

## Acknowledgments

- PyTorch team for the neural network framework
- Verilog-A community for modeling standards
- SPICE simulator developers for simulation support
