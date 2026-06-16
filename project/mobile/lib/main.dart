import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'providers/auth_provider.dart';
import 'screens/login_screen.dart';
import 'screens/registration_screen.dart';
import 'screens/patient/patient_home_screen.dart';
import 'screens/patient/appointment_booking_screen.dart';
import 'screens/patient/queue_status_screen.dart';
import 'screens/patient/medical_history_screen.dart';
import 'screens/doctor/doctor_home_screen.dart';
import 'screens/doctor/queue_management_screen.dart';
import 'screens/doctor/consultation_screen.dart';
import 'screens/doctor/patient_search_screen.dart';
import 'screens/doctor/allergies_screen.dart';
import 'screens/patient/procedures_screen.dart';
import 'screens/admin/organizations_screen.dart';
import 'screens/admin/providers_screen.dart';
import 'screens/nurse/vitals_entry_screen.dart';
import 'screens/patient/vitals_history_screen.dart';
import 'screens/nurse/nurse_home_screen.dart';
import 'screens/nurse/walk_in_registration_screen.dart';
import 'screens/admin/admin_home_screen.dart';
import 'screens/admin/user_management_screen.dart';
import 'screens/admin/audit_dashboard_screen.dart';
import 'models/appointment.dart';

void main() {
  runApp(const HealthSaathiApp());
}

class HealthSaathiApp extends StatelessWidget {
  const HealthSaathiApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider(),
      child: MaterialApp(
        title: 'HealthSaathi',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorScheme: ColorScheme.fromSeed(seedColor: Colors.blue),
          useMaterial3: true,
        ),
        initialRoute: '/',
        onGenerateRoute: (settings) {
          // Handle routes with arguments
          if (settings.name == '/queue-status') {
            final args = settings.arguments as Map<String, dynamic>?;
            if (args != null) {
              return MaterialPageRoute(
                builder: (context) => QueueStatusScreen(
                  doctorId: args['doctorId'] as int,
                  doctorName: args['doctorName'] as String?,
                ),
              );
            }
          }
          if (settings.name == '/doctor/consultation') {
            final args = settings.arguments as Map<String, dynamic>?;
            if (args != null && args['appointment'] != null) {
              return MaterialPageRoute(
                builder: (context) => ConsultationScreen(
                  appointment: args['appointment'] as Appointment,
                ),
              );
            }
          }
          if (settings.name == '/vitals/entry') {
            final args = settings.arguments as Map<String, dynamic>?;
            final patientId = args?['patientId'] as int?;
            return MaterialPageRoute(
              builder: (context) => VitalsEntryScreen(patientId: patientId),
            );
          }
          if (settings.name == '/vitals/history') {
            final args = settings.arguments as Map<String, dynamic>?;
            final patientId = args?['patientId'] as int?;
            final patientName = args?['patientName'] as String?;
            return MaterialPageRoute(
              builder: (context) => VitalsHistoryScreen(
                patientId: patientId,
                patientName: patientName,
              ),
            );
          }
          if (settings.name == '/allergies') {
            final args = settings.arguments as Map<String, dynamic>?;
            final patientId = args?['patientId'] as int? ?? 0;
            final patientName = args?['patientName'] as String?;
            return MaterialPageRoute(
              builder: (context) => AllergiesScreen(
                patientId: patientId,
                patientName: patientName,
              ),
            );
          }
          if (settings.name == '/procedures') {
            final args = settings.arguments as Map<String, dynamic>?;
            final patientId = args?['patientId'] as int?;
            final patientName = args?['patientName'] as String?;
            return MaterialPageRoute(
              builder: (context) => ProceduresScreen(
                patientId: patientId,
                patientName: patientName,
              ),
            );
          }
          return null;
        },
        routes: {
          '/': (context) => const SplashScreen(),
          '/login': (context) => const LoginScreen(),
          '/register': (context) => const RegistrationScreen(),
          '/patient-home': (context) => const PatientHomeScreen(),
          '/doctor-home': (context) => const DoctorHomeScreen(),
          '/nurse-home': (context) => const NurseHomeScreen(),
          '/admin-home': (context) => const AdminHomeScreen(),
          '/nurse/walk-in-registration': (context) => const WalkInRegistrationScreen(),
          '/doctor/queue-management': (context) => const QueueManagementScreen(),
          '/doctor/patient-search': (context) => const PatientSearchScreen(),
          '/appointment-booking': (context) => const AppointmentBookingScreen(),
          '/medical-history': (context) => const MedicalHistoryScreen(),
          '/admin/user-management': (context) => const UserManagementScreen(),
          '/admin/audit-dashboard': (context) => const AuditDashboardScreen(),
          '/admin/organizations': (context) => const OrganizationsScreen(),
          '/admin/providers': (context) => const ProvidersScreen(),
        },
      ),
    );
  }
}

class SplashScreen extends StatefulWidget {
  const SplashScreen({super.key});

  @override
  State<SplashScreen> createState() => _SplashScreenState();
}

class _SplashScreenState extends State<SplashScreen> {
  @override
  void initState() {
    super.initState();
    // Delay auth check to after first frame is built
    Future.delayed(const Duration(milliseconds: 500), () {
      if (mounted) {
        _checkAuth();
      }
    });
  }

  Future<void> _checkAuth() async {
    final authProvider = Provider.of<AuthProvider>(context, listen: false);
    await authProvider.initialize();

    if (mounted) {
      if (authProvider.isAuthenticated) {
        final user = authProvider.currentUser;
        if (user != null) {
          // Navigate based on user role
          if (user.isPatient) {
            Navigator.of(context).pushReplacementNamed('/patient-home');
          } else if (user.isDoctor) {
            Navigator.of(context).pushReplacementNamed('/doctor-home');
          } else if (user.isNurse) {
            Navigator.of(context).pushReplacementNamed('/nurse-home');
          } else if (user.isAdmin) {
            Navigator.of(context).pushReplacementNamed('/admin-home');
          } else {
            Navigator.of(context).pushReplacementNamed('/login');
          }
        } else {
          Navigator.of(context).pushReplacementNamed('/login');
        }
      } else {
        Navigator.of(context).pushReplacementNamed('/login');
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.local_hospital,
              size: 100,
              color: Theme.of(context).colorScheme.primary,
            ),
            const SizedBox(height: 20),
            const Text(
              'HealthSaathi',
              style: TextStyle(
                fontSize: 32,
                fontWeight: FontWeight.bold,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'Secure Healthcare Management',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
            ),
            const SizedBox(height: 40),
            const CircularProgressIndicator(),
          ],
        ),
      ),
    );
  }
}
