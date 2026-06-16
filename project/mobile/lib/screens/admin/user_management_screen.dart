import 'package:flutter/material.dart';
import '../../services/admin_service.dart';
import '../../models/user.dart';
import '../../widgets/loading_indicator.dart';
import '../../widgets/error_message.dart';

/// User management screen for admins to manage system users
class UserManagementScreen extends StatefulWidget {
  const UserManagementScreen({super.key});

  @override
  State<UserManagementScreen> createState() => _UserManagementScreenState();
}

class _UserManagementScreenState extends State<UserManagementScreen> {
  final AdminService _adminService = AdminService();
  final TextEditingController _searchController = TextEditingController();
  
  List<Map<String, dynamic>> _allUsers = [];
  List<Map<String, dynamic>> _filteredUsers = [];
  bool _isLoading = true;
  String? _error;
  String? _selectedRoleFilter;

  @override
  void initState() {
    super.initState();
    _loadUsers();
    _searchController.addListener(_filterUsers);
  }

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  /// Load all users from the API
  Future<void> _loadUsers() async {
    setState(() {
      _isLoading = true;
      _error = null;
    });

    try {
      final users = await _adminService.getAllUsers();
      setState(() {
        _allUsers = users;
        _filteredUsers = users;
        _isLoading = false;
      });
    } catch (e) {
      setState(() {
        _error = e.toString();
        _isLoading = false;
      });
    }
  }

  /// Filter users based on search query and role filter
  void _filterUsers() {
    final query = _searchController.text.toLowerCase();
    
    setState(() {
      _filteredUsers = _allUsers.where((user) {
        final name = (user['name'] as String? ?? '').toLowerCase();
        final email = (user['email'] as String? ?? '').toLowerCase();
        final role = user['role'] as String? ?? '';
        
        // Apply search filter
        final matchesSearch = query.isEmpty || 
            name.contains(query) || 
            email.contains(query);
        
        // Apply role filter
        final matchesRole = _selectedRoleFilter == null || 
            role == _selectedRoleFilter;
        
        return matchesSearch && matchesRole;
      }).toList();
    });
  }

  /// Show create user dialog
  void _showCreateUserDialog() {
    showDialog(
      context: context,
      builder: (context) => _UserFormDialog(
        onSave: (userData) async {
          try {
            await _adminService.createUser(
              name: userData['name'] as String,
              email: userData['email'] as String,
              password: userData['password'] as String,
              role: userData['role'] as String,
            );
            if (mounted) {
              Navigator.of(context).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('User created successfully')),
              );
              _loadUsers();
            }
          } catch (e) {
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Failed to create user: $e')),
              );
            }
          }
        },
      ),
    );
  }

  /// Show edit user dialog
  void _showEditUserDialog(Map<String, dynamic> user) {
    showDialog(
      context: context,
      builder: (context) => _UserFormDialog(
        user: user,
        onSave: (userData) async {
          try {
            await _adminService.updateUser(
              userId: user['id'] as int,
              name: userData['name'] as String,
              email: userData['email'] as String,
              role: userData['role'] as String,
            );
            if (mounted) {
              Navigator.of(context).pop();
              ScaffoldMessenger.of(context).showSnackBar(
                const SnackBar(content: Text('User updated successfully')),
              );
              _loadUsers();
            }
          } catch (e) {
            if (mounted) {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(content: Text('Failed to update user: $e')),
              );
            }
          }
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('User Management'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: _loadUsers,
            tooltip: 'Refresh',
          ),
        ],
      ),
      body: Column(
        children: [
          _buildSearchAndFilter(),
          Expanded(
            child: _buildBody(),
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: _showCreateUserDialog,
        tooltip: 'Create User',
        child: const Icon(Icons.person_add),
      ),
    );
  }

  Widget _buildSearchAndFilter() {
    return Container(
      padding: const EdgeInsets.all(16.0),
      color: Theme.of(context).colorScheme.surface,
      child: Column(
        children: [
          // Search bar
          TextField(
            controller: _searchController,
            decoration: InputDecoration(
              hintText: 'Search by name or email...',
              prefixIcon: const Icon(Icons.search),
              suffixIcon: _searchController.text.isNotEmpty
                  ? IconButton(
                      icon: const Icon(Icons.clear),
                      onPressed: () {
                        _searchController.clear();
                      },
                    )
                  : null,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(12),
              ),
              filled: true,
              fillColor: Theme.of(context).colorScheme.background,
            ),
          ),
          const SizedBox(height: 12),
          // Role filter chips
          SingleChildScrollView(
            scrollDirection: Axis.horizontal,
            child: Row(
              children: [
                _buildFilterChip('All', null),
                const SizedBox(width: 8),
                _buildFilterChip('Admin', 'Admin'),
                const SizedBox(width: 8),
                _buildFilterChip('Doctor', 'Doctor'),
                const SizedBox(width: 8),
                _buildFilterChip('Nurse', 'Nurse'),
                const SizedBox(width: 8),
                _buildFilterChip('Patient', 'Patient'),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildFilterChip(String label, String? role) {
    final isSelected = _selectedRoleFilter == role;
    
    return FilterChip(
      label: Text(label),
      selected: isSelected,
      onSelected: (selected) {
        setState(() {
          _selectedRoleFilter = selected ? role : null;
          _filterUsers();
        });
      },
      selectedColor: Theme.of(context).colorScheme.primaryContainer,
    );
  }

  Widget _buildBody() {
    if (_isLoading) {
      return const LoadingIndicator(message: 'Loading users...');
    }

    if (_error != null) {
      return ErrorMessage(
        message: _error!,
        onRetry: _loadUsers,
      );
    }

    if (_filteredUsers.isEmpty) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.people_outline,
              size: 64,
              color: Colors.grey[400],
            ),
            const SizedBox(height: 16),
            Text(
              _searchController.text.isNotEmpty || _selectedRoleFilter != null
                  ? 'No users found'
                  : 'No users yet',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey[600],
              ),
            ),
          ],
        ),
      );
    }

    return RefreshIndicator(
      onRefresh: _loadUsers,
      child: ListView.builder(
        padding: const EdgeInsets.all(16.0),
        itemCount: _filteredUsers.length,
        itemBuilder: (context, index) {
          final user = _filteredUsers[index];
          return _buildUserCard(user);
        },
      ),
    );
  }

  Widget _buildUserCard(Map<String, dynamic> user) {
    final name = user['name'] as String? ?? 'Unknown';
    final email = user['email'] as String? ?? '';
    final role = user['role'] as String? ?? 'User';
    final createdAt = DateTime.parse(user['created_at'] as String);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        contentPadding: const EdgeInsets.all(16),
        leading: CircleAvatar(
          radius: 24,
          backgroundColor: _getRoleColor(role).withOpacity(0.2),
          child: Text(
            name.isNotEmpty ? name[0].toUpperCase() : 'U',
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: _getRoleColor(role),
            ),
          ),
        ),
        title: Text(
          name,
          style: const TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.bold,
          ),
        ),
        subtitle: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const SizedBox(height: 4),
            Text(
              email,
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey[600],
              ),
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                _buildRoleBadge(role),
                const SizedBox(width: 8),
                Text(
                  'Joined ${_formatDate(createdAt)}',
                  style: TextStyle(
                    fontSize: 12,
                    color: Colors.grey[500],
                  ),
                ),
              ],
            ),
          ],
        ),
        trailing: IconButton(
          icon: const Icon(Icons.edit),
          onPressed: () => _showEditUserDialog(user),
          tooltip: 'Edit User',
        ),
      ),
    );
  }

  Widget _buildRoleBadge(String role) {
    final color = _getRoleColor(role);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: color.withOpacity(0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color, width: 1),
      ),
      child: Text(
        role,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.w600,
          color: color,
        ),
      ),
    );
  }

  Color _getRoleColor(String role) {
    switch (role) {
      case 'Admin':
        return Colors.red;
      case 'Doctor':
        return Colors.purple;
      case 'Nurse':
        return Colors.green;
      case 'Patient':
        return Colors.blue;
      default:
        return Colors.grey;
    }
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays == 0) {
      return 'today';
    } else if (difference.inDays == 1) {
      return 'yesterday';
    } else if (difference.inDays < 7) {
      return '${difference.inDays} days ago';
    } else if (difference.inDays < 30) {
      final weeks = (difference.inDays / 7).floor();
      return '$weeks ${weeks == 1 ? 'week' : 'weeks'} ago';
    } else if (difference.inDays < 365) {
      final months = (difference.inDays / 30).floor();
      return '$months ${months == 1 ? 'month' : 'months'} ago';
    } else {
      final years = (difference.inDays / 365).floor();
      return '$years ${years == 1 ? 'year' : 'years'} ago';
    }
  }
}

/// Dialog for creating or editing a user
class _UserFormDialog extends StatefulWidget {
  final Map<String, dynamic>? user;
  final Future<void> Function(Map<String, dynamic>) onSave;

  const _UserFormDialog({
    this.user,
    required this.onSave,
  });

  @override
  State<_UserFormDialog> createState() => _UserFormDialogState();
}

class _UserFormDialogState extends State<_UserFormDialog> {
  final _formKey = GlobalKey<FormState>();
  final _nameController = TextEditingController();
  final _emailController = TextEditingController();
  final _passwordController = TextEditingController();
  String _selectedRole = 'Patient';
  bool _isLoading = false;
  bool _obscurePassword = true;

  @override
  void initState() {
    super.initState();
    if (widget.user != null) {
      _nameController.text = widget.user!['name'] as String? ?? '';
      _emailController.text = widget.user!['email'] as String? ?? '';
      _selectedRole = widget.user!['role'] as String? ?? 'Patient';
    }
  }

  @override
  void dispose() {
    _nameController.dispose();
    _emailController.dispose();
    _passwordController.dispose();
    super.dispose();
  }

  bool get _isEditMode => widget.user != null;

  Future<void> _handleSave() async {
    if (!_formKey.currentState!.validate()) {
      return;
    }

    setState(() {
      _isLoading = true;
    });

    final userData = {
      'name': _nameController.text.trim(),
      'email': _emailController.text.trim(),
      'role': _selectedRole,
      if (!_isEditMode && _passwordController.text.isNotEmpty)
        'password': _passwordController.text,
    };

    try {
      await widget.onSave(userData);
    } finally {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(_isEditMode ? 'Edit User' : 'Create New User'),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Name field
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Name',
                  hintText: 'Enter full name',
                  prefixIcon: Icon(Icons.person),
                  border: OutlineInputBorder(),
                ),
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Name is required';
                  }
                  if (value.trim().length < 2) {
                    return 'Name must be at least 2 characters';
                  }
                  return null;
                },
                enabled: !_isLoading,
              ),
              const SizedBox(height: 16),
              
              // Email field
              TextFormField(
                controller: _emailController,
                decoration: const InputDecoration(
                  labelText: 'Email',
                  hintText: 'Enter email address',
                  prefixIcon: Icon(Icons.email),
                  border: OutlineInputBorder(),
                ),
                keyboardType: TextInputType.emailAddress,
                validator: (value) {
                  if (value == null || value.trim().isEmpty) {
                    return 'Email is required';
                  }
                  final emailRegex = RegExp(r'^[\w-\.]+@([\w-]+\.)+[\w-]{2,4}$');
                  if (!emailRegex.hasMatch(value.trim())) {
                    return 'Enter a valid email address';
                  }
                  return null;
                },
                enabled: !_isLoading,
              ),
              const SizedBox(height: 16),
              
              // Password field (only for create mode)
              if (!_isEditMode) ...[
                TextFormField(
                  controller: _passwordController,
                  decoration: InputDecoration(
                    labelText: 'Password',
                    hintText: 'Enter password',
                    prefixIcon: const Icon(Icons.lock),
                    suffixIcon: IconButton(
                      icon: Icon(
                        _obscurePassword ? Icons.visibility : Icons.visibility_off,
                      ),
                      onPressed: () {
                        setState(() {
                          _obscurePassword = !_obscurePassword;
                        });
                      },
                    ),
                    border: const OutlineInputBorder(),
                  ),
                  obscureText: _obscurePassword,
                  validator: (value) {
                    if (value == null || value.isEmpty) {
                      return 'Password is required';
                    }
                    if (value.length < 8) {
                      return 'Password must be at least 8 characters';
                    }
                    if (!value.contains(RegExp(r'[A-Z]'))) {
                      return 'Password must contain an uppercase letter';
                    }
                    if (!value.contains(RegExp(r'[a-z]'))) {
                      return 'Password must contain a lowercase letter';
                    }
                    if (!value.contains(RegExp(r'[0-9]'))) {
                      return 'Password must contain a number';
                    }
                    return null;
                  },
                  enabled: !_isLoading,
                ),
                const SizedBox(height: 16),
              ],
              
              // Role selection
              const Text(
                'Role',
                style: TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const SizedBox(height: 8),
              DropdownButtonFormField<String>(
                value: _selectedRole,
                decoration: const InputDecoration(
                  prefixIcon: Icon(Icons.badge),
                  border: OutlineInputBorder(),
                ),
                items: const [
                  DropdownMenuItem(value: 'Admin', child: Text('Admin')),
                  DropdownMenuItem(value: 'Doctor', child: Text('Doctor')),
                  DropdownMenuItem(value: 'Nurse', child: Text('Nurse')),
                  DropdownMenuItem(value: 'Patient', child: Text('Patient')),
                ],
                onChanged: _isLoading
                    ? null
                    : (value) {
                        setState(() {
                          _selectedRole = value!;
                        });
                      },
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: _isLoading ? null : () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isLoading ? null : _handleSave,
          child: _isLoading
              ? const SizedBox(
                  width: 20,
                  height: 20,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : Text(_isEditMode ? 'Update' : 'Create'),
        ),
      ],
    );
  }
}
