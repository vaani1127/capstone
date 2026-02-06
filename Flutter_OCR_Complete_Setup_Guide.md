# Complete Flutter OCR Implementation - Step-by-Step Guide

## STEP 1: Create Flutter Project

### Command:
```bash
flutter create mediflow_app
cd mediflow_app
```

### What this does:
- Creates a new Flutter project named `mediflow_app`
- Sets up the basic project structure with Android, iOS, and web support
- Creates the `lib` folder where all your code will go

---

## STEP 2: Update pubspec.yaml

### Open the file:
`mediflow_app/pubspec.yaml`

### Replace the entire file with this code:

```yaml
name: mediflow_app
description: Medical Form Digitization with OCR
publish_to: 'none'

version: 1.0.0+1

environment:
  sdk: '>=3.0.0 <4.0.0'

dependencies:
  flutter:
    sdk: flutter
  
  # UI & Navigation
  cupertino_icons: ^1.0.2
  get: ^4.6.5
  
  # Image Handling
  image_picker: ^1.0.4
  cached_network_image: ^3.3.0
  
  # API & Networking
  http: ^1.1.0
  dio: ^5.3.1
  
  # JSON Serialization
  json_serializable: ^6.7.0
  json_annotation: ^4.8.1
  
  # State Management
  provider: ^6.0.0
  
  # Local Storage
  shared_preferences: ^2.2.0
  hive: ^2.2.3
  hive_flutter: ^1.1.0
  
  # Utilities
  intl: ^0.19.0
  uuid: ^4.0.0
  logger: ^2.0.1
  
  # File Handling
  path_provider: ^2.1.0
  file_picker: ^6.0.0

dev_dependencies:
  flutter_test:
    sdk: flutter
  flutter_lints: ^3.0.0
  build_runner: ^2.4.6
  json_serializable: ^6.7.0

flutter:
  uses-material-design: true
```

### Save the file

---

## STEP 3: Install Dependencies

### Command:
```bash
flutter pub get
```

### What this does:
- Downloads and installs all the packages listed in pubspec.yaml
- This may take 2-5 minutes depending on your internet speed

---

## STEP 4: Create Folder Structure

### Create these folders inside the `lib` directory:

```
lib/
├── models/
├── services/
├── providers/
├── screens/
├── widgets/
└── utils/
```

### Commands to create folders:
```bash
mkdir -p lib/models
mkdir -p lib/services
mkdir -p lib/providers
mkdir -p lib/screens
mkdir -p lib/widgets
mkdir -p lib/utils
```

---

## STEP 5: Create Models File

### File Path: `lib/models/ocr_models.dart`

### Copy and paste this entire code:

```dart
import 'package:json_annotation/json_annotation.dart';

part 'ocr_models.g.dart';

@JsonSerializable()
class Medication {
  final String name;
  final String dosage;
  final String frequency;
  final String? route;
  final double confidence;

  Medication({
    required this.name,
    required this.dosage,
    required this.frequency,
    this.route,
    required this.confidence,
  });

  factory Medication.fromJson(Map<String, dynamic> json) =>
      _$MedicationFromJson(json);
  Map<String, dynamic> toJson() => _$MedicationToJson(this);
}

@JsonSerializable()
class Allergy {
  final String allergen;
  final String severity;
  final String? reaction;
  final double confidence;

  Allergy({
    required this.allergen,
    required this.severity,
    this.reaction,
    required this.confidence,
  });

  factory Allergy.fromJson(Map<String, dynamic> json) =>
      _$AllergyFromJson(json);
  Map<String, dynamic> toJson() => _$AllergyToJson(this);
}

@JsonSerializable()
class Diagnosis {
  final String condition;
  final String? icdCode;
  final String? status;
  final double confidence;

  Diagnosis({
    required this.condition,
    this.icdCode,
    this.status,
    required this.confidence,
  });

  factory Diagnosis.fromJson(Map<String, dynamic> json) =>
      _$DiagnosisFromJson(json);
  Map<String, dynamic> toJson() => _$DiagnosisToJson(this);
}

@JsonSerializable()
class PatientInfo {
  final String? name;
  final String? age;
  final String? gender;
  final String? mrn;
  final String? dateOfBirth;

  PatientInfo({
    this.name,
    this.age,
    this.gender,
    this.mrn,
    this.dateOfBirth,
  });

  factory PatientInfo.fromJson(Map<String, dynamic> json) =>
      _$PatientInfoFromJson(json);
  Map<String, dynamic> toJson() => _$PatientInfoToJson(this);
}

@JsonSerializable()
class OCRExtractionResult {
  final String rawText;
  final List<Medication> medications;
  final List<Allergy> allergies;
  final List<Diagnosis> diagnoses;
  final PatientInfo patientInfo;
  final double extractionAccuracy;
  final String? doctorName;
  final DateTime? extractedAt;

  OCRExtractionResult({
    required this.rawText,
    required this.medications,
    required this.allergies,
    required this.diagnoses,
    required this.patientInfo,
    required this.extractionAccuracy,
    this.doctorName,
    this.extractedAt,
  });

  factory OCRExtractionResult.fromJson(Map<String, dynamic> json) =>
      _$OCRExtractionResultFromJson(json);
  Map<String, dynamic> toJson() => _$OCRExtractionResultToJson(this);
}

@JsonSerializable()
class UploadResponse {
  final bool success;
  final String? message;
  final OCRExtractionResult? data;
  final String? error;

  UploadResponse({
    required this.success,
    this.message,
    this.data,
    this.error,
  });

  factory UploadResponse.fromJson(Map<String, dynamic> json) =>
      _$UploadResponseFromJson(json);
  Map<String, dynamic> toJson() => _$UploadResponseToJson(this);
}
```

### Save the file

---

## STEP 6: Generate JSON Serialization Code

### Command:
```bash
flutter pub run build_runner build
```

### What this does:
- Automatically generates the `ocr_models.g.dart` file
- This file contains the JSON serialization code
- Wait for it to complete (should say "Succeeded")

---

## STEP 7: Create API Service File

### File Path: `lib/services/ocr_api_service.dart`

### Copy and paste this entire code:

```dart
import 'dart:convert';
import 'dart:io';
import 'package:dio/dio.dart';
import 'package:logger/logger.dart';
import '../models/ocr_models.dart';

class OCRApiService {
  final String baseUrl;
  late final Dio _dio;
  final logger = Logger();

  OCRApiService({
    required this.baseUrl,
  }) {
    _dio = Dio(
      BaseOptions(
        baseUrl: baseUrl,
        connectTimeout: const Duration(seconds: 30),
        receiveTimeout: const Duration(seconds: 60),
        contentType: 'application/json',
      ),
    );

    _dio.interceptors.add(
      LoggingInterceptor(logger),
    );
  }

  /// Upload prescription image and get OCR extraction
  Future<OCRExtractionResult> uploadPrescriptionImage({
    required File imageFile,
    required String fileName,
  }) async {
    try {
      // Convert image to base64
      final imageBytes = await imageFile.readAsBytes();
      final base64Image = base64Encode(imageBytes);

      logger.i('Uploading image: $fileName');

      // Prepare request
      final response = await _dio.post(
        '/api/trpc/mediflow.uploadPrescriptionImage',
        data: {
          'imageBase64': base64Image,
          'fileName': fileName,
          'mimeType': 'image/png',
        },
      );

      logger.i('Response status: ${response.statusCode}');

      if (response.statusCode == 200) {
        // Parse response
        final data = response.data;
        
        // Handle tRPC response format
        if (data is List && data.isNotEmpty) {
          final result = data[0];
          if (result['result'] != null) {
            final extractionData = result['result']['data']['json'];
            logger.i('Extraction successful');
            return OCRExtractionResult.fromJson(extractionData);
          }
        }

        throw Exception('Invalid response format');
      } else {
        throw Exception('Upload failed with status ${response.statusCode}');
      }
    } on DioException catch (e) {
      logger.e('DioException: ${e.message}');
      throw Exception('Network error: ${e.message}');
    } catch (e) {
      logger.e('Error uploading prescription: $e');
      throw Exception('Error uploading prescription: $e');
    }
  }

  /// Validate extraction results
  Future<OCRExtractionResult> validateExtraction({
    required OCRExtractionResult extraction,
  }) async {
    try {
      logger.i('Validating extraction');

      final response = await _dio.post(
        '/api/trpc/mediflow.validateExtraction',
        data: extraction.toJson(),
      );

      if (response.statusCode == 200) {
        final data = response.data;
        if (data is List && data.isNotEmpty) {
          final result = data[0];
          if (result['result'] != null) {
            final validatedData = result['result']['data']['json'];
            logger.i('Validation successful');
            return OCRExtractionResult.fromJson(validatedData);
          }
        }
        return extraction;
      } else {
        throw Exception('Validation failed');
      }
    } catch (e) {
      logger.e('Error validating extraction: $e');
      return extraction;
    }
  }

  /// Convert to FHIR format
  Future<Map<String, dynamic>> convertToFHIR({
    required OCRExtractionResult extraction,
  }) async {
    try {
      logger.i('Converting to FHIR');

      final response = await _dio.post(
        '/api/trpc/mediflow.convertToFHIR',
        data: extraction.toJson(),
      );

      if (response.statusCode == 200) {
        final data = response.data;
        if (data is List && data.isNotEmpty) {
          final result = data[0];
          if (result['result'] != null) {
            logger.i('FHIR conversion successful');
            return result['result']['data']['json'];
          }
        }
      }

      return {};
    } catch (e) {
      logger.e('Error converting to FHIR: $e');
      return {};
    }
  }
}

class LoggingInterceptor extends Interceptor {
  final Logger logger;

  LoggingInterceptor(this.logger);

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    logger.i('REQUEST: ${options.method} ${options.path}');
    super.onRequest(options, handler);
  }

  @override
  void onResponse(Response response, ResponseInterceptorHandler handler) {
    logger.i('RESPONSE: ${response.statusCode} ${response.requestOptions.path}');
    super.onResponse(response, handler);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    logger.e('ERROR: ${err.message}');
    super.onError(err, handler);
  }
}
```

### Save the file

---

## STEP 8: Create State Management File

### File Path: `lib/providers/ocr_provider.dart`

### Copy and paste this entire code:

```dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:logger/logger.dart';
import '../models/ocr_models.dart';
import '../services/ocr_api_service.dart';

class OCRProvider extends ChangeNotifier {
  final OCRApiService apiService;
  final logger = Logger();

  OCRProvider({required this.apiService});

  // State variables
  OCRExtractionResult? _lastExtraction;
  bool _isLoading = false;
  String? _error;
  File? _selectedImage;
  Map<String, dynamic>? _fhirData;
  double _uploadProgress = 0;

  // Getters
  OCRExtractionResult? get lastExtraction => _lastExtraction;
  bool get isLoading => _isLoading;
  String? get error => _error;
  File? get selectedImage => _selectedImage;
  Map<String, dynamic>? get fhirData => _fhirData;
  double get uploadProgress => _uploadProgress;

  // Set selected image
  void setSelectedImage(File image) {
    _selectedImage = image;
    _error = null;
    _uploadProgress = 0;
    notifyListeners();
  }

  // Clear selection
  void clearSelection() {
    _selectedImage = null;
    _lastExtraction = null;
    _fhirData = null;
    _error = null;
    _uploadProgress = 0;
    notifyListeners();
  }

  // Upload and extract
  Future<void> uploadAndExtract() async {
    if (_selectedImage == null) {
      _error = 'Please select an image first';
      notifyListeners();
      return;
    }

    _isLoading = true;
    _error = null;
    _uploadProgress = 0;
    notifyListeners();

    try {
      // Step 1: Upload and extract
      _uploadProgress = 0.3;
      notifyListeners();
      
      _lastExtraction = await apiService.uploadPrescriptionImage(
        imageFile: _selectedImage!,
        fileName: _selectedImage!.path.split('/').last,
      );

      // Step 2: Validate extraction
      _uploadProgress = 0.6;
      notifyListeners();
      
      _lastExtraction = await apiService.validateExtraction(
        extraction: _lastExtraction!,
      );

      // Step 3: Convert to FHIR
      _uploadProgress = 0.9;
      notifyListeners();
      
      _fhirData = await apiService.convertToFHIR(
        extraction: _lastExtraction!,
      );

      _uploadProgress = 1.0;
      logger.i('Extraction successful: ${_lastExtraction?.medications.length} medications found');
    } catch (e) {
      _error = e.toString();
      logger.e('Error during extraction: $e');
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  // Clear error
  void clearError() {
    _error = null;
    notifyListeners();
  }
}
```

### Save the file

---

## STEP 9: Create Main Upload Screen

### File Path: `lib/screens/ocr_upload_screen.dart`

### Copy and paste this entire code:

```dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:provider/provider.dart';
import '../providers/ocr_provider.dart';
import '../widgets/extraction_results_widget.dart';

class OCRUploadScreen extends StatefulWidget {
  const OCRUploadScreen({Key? key}) : super(key: key);

  @override
  State<OCRUploadScreen> createState() => _OCRUploadScreenState();
}

class _OCRUploadScreenState extends State<OCRUploadScreen> {
  final ImagePicker _imagePicker = ImagePicker();

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Upload Prescription'),
        elevation: 0,
        backgroundColor: Colors.blue,
      ),
      body: Consumer<OCRProvider>(
        builder: (context, ocrProvider, _) {
          return SingleChildScrollView(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                // Header
                const Text(
                  'Upload Medical Form',
                  style: TextStyle(
                    fontSize: 24,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                const SizedBox(height: 8),
                const Text(
                  'Capture or upload a prescription image to extract medical data',
                  style: TextStyle(
                    fontSize: 14,
                    color: Colors.grey,
                  ),
                ),
                const SizedBox(height: 24),

                // Image Selection or Preview
                if (ocrProvider.selectedImage == null)
                  _buildImageSelectionArea(context, ocrProvider)
                else
                  _buildImagePreview(context, ocrProvider),

                const SizedBox(height: 24),

                // Error Message
                if (ocrProvider.error != null)
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: Colors.red.shade50,
                      border: Border.all(color: Colors.red.shade300),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Row(
                      children: [
                        Icon(Icons.error_outline, color: Colors.red.shade700),
                        const SizedBox(width: 12),
                        Expanded(
                          child: Text(
                            ocrProvider.error ?? '',
                            style: TextStyle(color: Colors.red.shade700),
                          ),
                        ),
                        IconButton(
                          icon: const Icon(Icons.close),
                          onPressed: ocrProvider.clearError,
                        ),
                      ],
                    ),
                  ),

                const SizedBox(height: 24),

                // Upload Button
                if (ocrProvider.selectedImage != null && !ocrProvider.isLoading)
                  ElevatedButton.icon(
                    onPressed: ocrProvider.uploadAndExtract,
                    icon: const Icon(Icons.cloud_upload),
                    label: const Text('Extract Data'),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      backgroundColor: Colors.blue,
                      foregroundColor: Colors.white,
                    ),
                  ),

                // Loading Indicator
                if (ocrProvider.isLoading)
                  Column(
                    children: [
                      LinearProgressIndicator(
                        value: ocrProvider.uploadProgress,
                        minHeight: 8,
                      ),
                      const SizedBox(height: 16),
                      Text(
                        'Processing: ${(ocrProvider.uploadProgress * 100).toStringAsFixed(0)}%',
                        style: const TextStyle(fontSize: 14),
                      ),
                      const SizedBox(height: 8),
                      const Text('Processing prescription...'),
                    ],
                  ),

                const SizedBox(height: 24),

                // Results
                if (ocrProvider.lastExtraction != null && !ocrProvider.isLoading)
                  ExtractionResultsWidget(
                    extraction: ocrProvider.lastExtraction!,
                    fhirData: ocrProvider.fhirData,
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  Widget _buildImageSelectionArea(
    BuildContext context,
    OCRProvider provider,
  ) {
    return Container(
      decoration: BoxDecoration(
        border: Border.all(color: Colors.blue.shade300, width: 2),
        borderRadius: BorderRadius.circular(12),
        color: Colors.blue.shade50,
      ),
      padding: const EdgeInsets.all(32),
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(
            Icons.image_not_supported_outlined,
            size: 64,
            color: Colors.blue.shade300,
          ),
          const SizedBox(height: 16),
          const Text(
            'No image selected',
            style: TextStyle(fontSize: 16, fontWeight: FontWeight.w500),
          ),
          const SizedBox(height: 24),
          Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              ElevatedButton.icon(
                onPressed: () => _pickImage(context, provider, ImageSource.camera),
                icon: const Icon(Icons.camera_alt),
                label: const Text('Take Photo'),
              ),
              const SizedBox(width: 12),
              ElevatedButton.icon(
                onPressed: () => _pickImage(context, provider, ImageSource.gallery),
                icon: const Icon(Icons.photo_library),
                label: const Text('Choose File'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildImagePreview(BuildContext context, OCRProvider provider) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(12),
          child: Image.file(
            provider.selectedImage!,
            height: 300,
            fit: BoxFit.cover,
          ),
        ),
        const SizedBox(height: 16),
        Row(
          children: [
            Expanded(
              child: OutlinedButton.icon(
                onPressed: () => provider.clearSelection(),
                icon: const Icon(Icons.close),
                label: const Text('Change Image'),
              ),
            ),
          ],
        ),
      ],
    );
  }

  Future<void> _pickImage(
    BuildContext context,
    OCRProvider provider,
    ImageSource source,
  ) async {
    try {
      final pickedFile = await _imagePicker.pickImage(source: source);
      if (pickedFile != null) {
        provider.setSelectedImage(File(pickedFile.path));
      }
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Error picking image: $e')),
      );
    }
  }
}
```

### Save the file

---

## STEP 10: Create Results Display Widget

### File Path: `lib/widgets/extraction_results_widget.dart`

### Copy and paste this entire code:

```dart
import 'package:flutter/material.dart';
import '../models/ocr_models.dart';

class ExtractionResultsWidget extends StatefulWidget {
  final OCRExtractionResult extraction;
  final Map<String, dynamic>? fhirData;

  const ExtractionResultsWidget({
    Key? key,
    required this.extraction,
    this.fhirData,
  }) : super(key: key);

  @override
  State<ExtractionResultsWidget> createState() =>
      _ExtractionResultsWidgetState();
}

class _ExtractionResultsWidgetState extends State<ExtractionResultsWidget>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 4, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        // Accuracy Badge
        Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.green.shade50,
            border: Border.all(color: Colors.green.shade300),
            borderRadius: BorderRadius.circular(8),
          ),
          child: Row(
            children: [
              Icon(Icons.check_circle, color: Colors.green.shade700),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Extraction Complete',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    Text(
                      'Accuracy: ${(widget.extraction.extractionAccuracy * 100).toStringAsFixed(1)}%',
                      style: const TextStyle(fontSize: 12),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Tabs
        TabBar(
          controller: _tabController,
          tabs: const [
            Tab(text: 'Medications'),
            Tab(text: 'Allergies'),
            Tab(text: 'Diagnoses'),
            Tab(text: 'Patient Info'),
          ],
        ),
        const SizedBox(height: 16),

        // Tab Content
        SizedBox(
          height: 400,
          child: TabBarView(
            controller: _tabController,
            children: [
              _buildMedicationsTab(),
              _buildAllergiesTab(),
              _buildDiagnosesTab(),
              _buildPatientInfoTab(),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildMedicationsTab() {
    if (widget.extraction.medications.isEmpty) {
      return const Center(
        child: Text('No medications found'),
      );
    }

    return ListView.builder(
      itemCount: widget.extraction.medications.length,
      itemBuilder: (context, index) {
        final med = widget.extraction.medications[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        med.name,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ),
                    Chip(
                      label: Text('${(med.confidence * 100).toStringAsFixed(0)}%'),
                      backgroundColor: Colors.blue.shade100,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                Text('Dosage: ${med.dosage}'),
                Text('Frequency: ${med.frequency}'),
                if (med.route != null) Text('Route: ${med.route}'),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildAllergiesTab() {
    if (widget.extraction.allergies.isEmpty) {
      return const Center(
        child: Text('No allergies found'),
      );
    }

    return ListView.builder(
      itemCount: widget.extraction.allergies.length,
      itemBuilder: (context, index) {
        final allergy = widget.extraction.allergies[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          color: _getSeverityColor(allergy.severity),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        allergy.allergen,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ),
                    Chip(
                      label: Text(allergy.severity),
                      backgroundColor: Colors.white,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                if (allergy.reaction != null) Text('Reaction: ${allergy.reaction}'),
                Text('Confidence: ${(allergy.confidence * 100).toStringAsFixed(0)}%'),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildDiagnosesTab() {
    if (widget.extraction.diagnoses.isEmpty) {
      return const Center(
        child: Text('No diagnoses found'),
      );
    }

    return ListView.builder(
      itemCount: widget.extraction.diagnoses.length,
      itemBuilder: (context, index) {
        final diagnosis = widget.extraction.diagnoses[index];
        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          child: Padding(
            padding: const EdgeInsets.all(12),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Expanded(
                      child: Text(
                        diagnosis.condition,
                        style: const TextStyle(
                          fontWeight: FontWeight.bold,
                          fontSize: 16,
                        ),
                      ),
                    ),
                    Chip(
                      label: Text('${(diagnosis.confidence * 100).toStringAsFixed(0)}%'),
                      backgroundColor: Colors.purple.shade100,
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                if (diagnosis.icdCode != null) Text('ICD Code: ${diagnosis.icdCode}'),
                if (diagnosis.status != null) Text('Status: ${diagnosis.status}'),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildPatientInfoTab() {
    final info = widget.extraction.patientInfo;
    return SingleChildScrollView(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          if (info.name != null)
            _buildInfoRow('Name', info.name ?? 'N/A'),
          if (info.age != null)
            _buildInfoRow('Age', info.age ?? 'N/A'),
          if (info.gender != null)
            _buildInfoRow('Gender', info.gender ?? 'N/A'),
          if (info.mrn != null)
            _buildInfoRow('MRN', info.mrn ?? 'N/A'),
          if (info.dateOfBirth != null)
            _buildInfoRow('Date of Birth', info.dateOfBirth ?? 'N/A'),
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        children: [
          SizedBox(
            width: 120,
            child: Text(
              label,
              style: const TextStyle(fontWeight: FontWeight.bold),
            ),
          ),
          Expanded(
            child: Text(value),
          ),
        ],
      ),
    );
  }

  Color _getSeverityColor(String severity) {
    switch (severity.toLowerCase()) {
      case 'severe':
        return Colors.red.shade100;
      case 'moderate':
        return Colors.orange.shade100;
      case 'mild':
        return Colors.yellow.shade100;
      default:
        return Colors.grey.shade100;
    }
  }
}
```

### Save the file

---

## STEP 11: Update Main.dart

### File Path: `lib/main.dart`

### Replace the entire file with this code:

```dart
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/ocr_api_service.dart';
import 'providers/ocr_provider.dart';
import 'screens/ocr_upload_screen.dart';

void main() {
  runApp(const MyApp());
}

class MyApp extends StatelessWidget {
  const MyApp({Key? key}) : super(key: key);

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        Provider<OCRApiService>(
          create: (_) => OCRApiService(
            // IMPORTANT: Replace this with your actual backend URL
            baseUrl: 'https://3000-i3h8aylu8tinptr5hbla8-53c98253.sg1.manus.computer',
          ),
        ),
        ChangeNotifierProvider(
          create: (context) => OCRProvider(
            apiService: context.read<OCRApiService>(),
          ),
        ),
      ],
      child: MaterialApp(
        title: 'MediFlow',
        theme: ThemeData(
          primarySwatch: Colors.blue,
          useMaterial3: true,
        ),
        home: const OCRUploadScreen(),
      ),
    );
  }
}
```

### Save the file

---

## STEP 12: Add Android Permissions

### File Path: `android/app/src/main/AndroidManifest.xml`

### Add these permissions inside the `<manifest>` tag (before `<application>`):

```xml
<uses-permission android:name="android.permission.CAMERA" />
<uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
<uses-permission android:name="android.permission.INTERNET" />
```

### Example of where to add it:
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.example.mediflow_app">

    <!-- ADD PERMISSIONS HERE -->
    <uses-permission android:name="android.permission.CAMERA" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.WRITE_EXTERNAL_STORAGE" />
    <uses-permission android:name="android.permission.INTERNET" />

    <application>
        ...
    </application>
</manifest>
```

---

## STEP 13: Add iOS Permissions

### File Path: `ios/Runner/Info.plist`

### Add these lines inside the `<dict>` tag:

```xml
<key>NSCameraUsageDescription</key>
<string>This app needs camera access to capture prescriptions</string>
<key>NSPhotoLibraryUsageDescription</key>
<string>This app needs photo library access to upload prescriptions</string>
<key>NSPhotoLibraryAddUsageDescription</key>
<string>This app needs permission to save photos</string>
```

### Example of where to add it:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <!-- ADD THESE LINES -->
    <key>NSCameraUsageDescription</key>
    <string>This app needs camera access to capture prescriptions</string>
    <key>NSPhotoLibraryUsageDescription</key>
    <string>This app needs photo library access to upload prescriptions</string>
    <key>NSPhotoLibraryAddUsageDescription</key>
    <string>This app needs permission to save photos</string>
    
    <!-- Rest of the file -->
    ...
</dict>
</plist>
```

---

## STEP 14: Run the App

### Command:
```bash
flutter run
```

### What this does:
- Compiles your Flutter app
- Installs it on your connected device or emulator
- Launches the app
- Shows logs in the terminal

### If you have multiple devices:
```bash
flutter devices  # List all devices
flutter run -d <device_id>  # Run on specific device
```

---

## STEP 15: Test the App

### Test Steps:

1. **Launch the app** - You should see the upload screen
2. **Click "Take Photo"** - Opens camera to capture prescription
3. **Or click "Choose File"** - Opens gallery to select image
4. **Select an image** - Image preview appears
5. **Click "Extract Data"** - Processing starts
6. **Wait for results** - Should show medications, allergies, diagnoses
7. **View different tabs** - Click tabs to see different data

---

## STEP 16: Update Backend URL (IMPORTANT!)

### In `lib/main.dart`, find this line:

```dart
baseUrl: 'https://3000-i3h8aylu8tinptr5hbla8-53c98253.sg1.manus.computer',
```

### Replace with your actual backend URL:

```dart
baseUrl: 'https://your-actual-backend-url.com',
```

### Or if using localhost during development:

```dart
baseUrl: 'http://192.168.1.100:3000', // Replace with your machine IP
```

---

## Common Issues & Solutions

### Issue 1: Build fails with "Unresolved reference"
**Solution:**
```bash
flutter clean
flutter pub get
flutter pub run build_runner build
```

### Issue 2: Image picker not working
**Solution:** Make sure permissions are added to AndroidManifest.xml and Info.plist

### Issue 3: API connection error
**Solution:** 
- Check backend URL is correct
- Make sure backend server is running
- Check internet connection

### Issue 4: JSON parsing error
**Solution:**
```bash
flutter pub run build_runner build --delete-conflicting-outputs
```

---

## Summary of Files Created

| File | Purpose |
|------|---------|
| `lib/main.dart` | App entry point and setup |
| `lib/models/ocr_models.dart` | Data models |
| `lib/services/ocr_api_service.dart` | Backend API calls |
| `lib/providers/ocr_provider.dart` | State management |
| `lib/screens/ocr_upload_screen.dart` | Main upload screen |
| `lib/widgets/extraction_results_widget.dart` | Results display |
| `pubspec.yaml` | Dependencies |
| `android/app/src/main/AndroidManifest.xml` | Android permissions |
| `ios/Runner/Info.plist` | iOS permissions |

---

## Next Steps

1. **Test with real prescriptions** - Upload actual prescription images
2. **Customize UI** - Modify colors, fonts, layouts
3. **Add more features** - Export to PDF, share results, etc.
4. **Deploy** - Build APK/IPA for distribution

---

## Need Help?

If you encounter any issues:

1. Check the console logs: `flutter run -v` for verbose output
2. Verify all files are created correctly
3. Make sure dependencies are installed: `flutter pub get`
4. Rebuild JSON serialization: `flutter pub run build_runner build`
5. Check backend server is running and accessible

Good luck with your Flutter OCR app! 🚀
