# patients/models.py
from django.db import models
from django.conf import settings
from django.utils import timezone
import hashlib
import json

class Patient(models.Model):
    """Extended patient profile"""
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='patient_profile')
    
    # Medical Information
    blood_type = models.CharField(max_length=5, choices=[
        ('A+', 'A+'), ('A-', 'A-'),
        ('B+', 'B+'), ('B-', 'B-'),
        ('AB+', 'AB+'), ('AB-', 'AB-'),
        ('O+', 'O+'), ('O-', 'O-'),
    ], blank=True)
    
    allergies = models.TextField(blank=True, help_text="List any allergies")
    chronic_conditions = models.TextField(blank=True)
    
    # Emergency Contact
    emergency_contact_name = models.CharField(max_length=100)
    emergency_contact_phone = models.CharField(max_length=15)
    emergency_contact_relation = models.CharField(max_length=50)
    
    # Insurance (can be encrypted later)
    insurance_provider = models.CharField(max_length=100, blank=True)
    insurance_number = models.CharField(max_length=50, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'patients'
    
    def __str__(self):
        return f"Patient: {self.user.get_full_name()}"


class MedicalRecord(models.Model):
    """
    Medical records with blockchain-ready hash verification
    Each record generates a hash for integrity checking
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='medical_records')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_records')
    
    # Record Details
    record_type = models.CharField(max_length=50, choices=[
        ('consultation', 'Consultation'),
        ('diagnosis', 'Diagnosis'),
        ('prescription', 'Prescription'),
        ('lab_result', 'Lab Result'),
        ('imaging', 'Imaging'),
        ('procedure', 'Procedure'),
        ('vaccination', 'Vaccination'),
    ])
    
    title = models.CharField(max_length=200)
    diagnosis = models.TextField()
    treatment = models.TextField()
    prescription = models.TextField(blank=True)
    notes = models.TextField(blank=True)
    
    # File attachment
    document = models.FileField(upload_to='medical_records/%Y/%m/', blank=True)
    
    # Metadata
    visit_date = models.DateField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Blockchain-ready fields
    record_hash = models.CharField(max_length=64, editable=False, unique=True)
    previous_hash = models.CharField(max_length=64, blank=True, editable=False)
    is_verified = models.BooleanField(default=False)
    blockchain_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Access Control
    is_active = models.BooleanField(default=True)
    shared_with = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='accessible_records', blank=True)
    
    class Meta:
        db_table = 'medical_records'
        ordering = ['-visit_date', '-created_at']
        indexes = [
            models.Index(fields=['patient', '-visit_date']),
            models.Index(fields=['record_hash']),
        ]
    
    def __str__(self):
        return f"{self.record_type}: {self.title} - {self.patient.user.get_full_name()}"
    
    def generate_hash(self):
        """
        Generate SHA-256 hash of record data for integrity verification
        This prepares the record for blockchain storage
        """
        # Get previous record's hash to create chain
        previous_record = MedicalRecord.objects.filter(
            patient=self.patient,
            created_at__lt=self.created_at
        ).order_by('-created_at').first()
        
        self.previous_hash = previous_record.record_hash if previous_record else '0' * 64
        
        # Create record data dictionary
        record_data = {
            'patient_id': self.patient.id,
            'created_by_id': self.created_by.id if self.created_by else None,
            'record_type': self.record_type,
            'title': self.title,
            'diagnosis': self.diagnosis,
            'treatment': self.treatment,
            'prescription': self.prescription,
            'visit_date': str(self.visit_date),
            'created_at': str(self.created_at),
            'previous_hash': self.previous_hash,
        }
        
        # Generate hash
        record_string = json.dumps(record_data, sort_keys=True)
        self.record_hash = hashlib.sha256(record_string.encode()).hexdigest()
        
        return self.record_hash
    
    def verify_integrity(self):
        """
        Verify record hasn't been tampered with by recalculating hash
        Returns True if record is valid
        """
        current_hash = self.record_hash
        self.generate_hash()
        calculated_hash = self.record_hash
        
        # Restore original hash
        self.record_hash = current_hash
        
        return current_hash == calculated_hash
    
    def save(self, *args, **kwargs):
        """Override save to generate hash on creation"""
        if not self.record_hash:
            # Temporary save to get timestamp
            if not self.pk:
                super().save(*args, **kwargs)
            self.generate_hash()
        super().save(*args, **kwargs)


class MedicalCertificate(models.Model):
    """
    Medical certificates issued to patients
    Also blockchain-ready with hash verification
    """
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name='certificates')
    issued_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='issued_certificates')
    
    certificate_type = models.CharField(max_length=50, choices=[
        ('sick_leave', 'Sick Leave'),
        ('fit_to_work', 'Fit to Work'),
        ('medical_clearance', 'Medical Clearance'),
        ('vaccination', 'Vaccination Certificate'),
        ('disability', 'Disability Certificate'),
    ])
    
    purpose = models.CharField(max_length=200)
    diagnosis = models.TextField()
    recommendations = models.TextField()
    
    # Validity period
    valid_from = models.DateField()
    valid_until = models.DateField()
    
    # Certificate file (PDF generated)
    certificate_file = models.FileField(upload_to='certificates/%Y/%m/', blank=True)
    
    # Metadata
    issued_at = models.DateTimeField(auto_now_add=True)
    
    # Blockchain-ready
    certificate_hash = models.CharField(max_length=64, editable=False, unique=True)
    is_verified = models.BooleanField(default=False)
    blockchain_transaction_id = models.CharField(max_length=100, blank=True, null=True)
    
    # Status
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('issued', 'Issued'),
        ('revoked', 'Revoked'),
    ], default='issued')
    
    class Meta:
        db_table = 'medical_certificates'
        ordering = ['-issued_at']
    
    def __str__(self):
        return f"{self.certificate_type} - {self.patient.user.get_full_name()}"
    
    def generate_hash(self):
        """Generate hash for certificate verification"""
        cert_data = {
            'patient_id': self.patient.id,
            'issued_by_id': self.issued_by.id if self.issued_by else None,
            'certificate_type': self.certificate_type,
            'purpose': self.purpose,
            'valid_from': str(self.valid_from),
            'valid_until': str(self.valid_until),
            'issued_at': str(self.issued_at),
        }
        
        cert_string = json.dumps(cert_data, sort_keys=True)
        self.certificate_hash = hashlib.sha256(cert_string.encode()).hexdigest()
        return self.certificate_hash
    
    def save(self, *args, **kwargs):
        if not self.certificate_hash:
            if not self.pk:
                super().save(*args, **kwargs)
            self.generate_hash()
        super().save(*args, **kwargs)


class RecordAccessLog(models.Model):
    """
    Log every access to medical records for HIPAA/compliance
    """
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='access_logs')
    accessed_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
    
    access_type = models.CharField(max_length=20, choices=[
        ('view', 'Viewed'),
        ('download', 'Downloaded'),
        ('share', 'Shared'),
        ('edit', 'Edited'),
    ])
    
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    accessed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'record_access_logs'
        ordering = ['-accessed_at']