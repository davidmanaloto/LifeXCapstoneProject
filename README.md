### Achievements
Authentication System
- MFA (development mode)
- Role-base access (patient, nurse, doctor)
- Audit logging
- Password Policies
- Execution Prevention (still need testing)
- Using SQlite for development

### Pending
Authentication System
- MFA tool not yet implemented
- Network segmentation
- Encrypt Sensitive Information
- Session token
- Block chain security
- Face recognition
- PostgreSQL Transfer


### 1. Clone Repository
```bash
git clone https://github.com/davidmanaloto/LifeXCapstoneProject.git
```

### 2. Locate Project Structure
```bash
mkdir hospital_portal
cd hospital_portal
```

### 3. Set Up Virtual Environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate
```
### 4. Install Requirements
```bash
pip install -r requirements.txt
```

### 5. Migrations
```bash
# Necssary migrations
python manage.py makemigrations accounts
python manage.py makemigrations patients
python manage.py makemigrations staff

# Apply migrations
python manage.py migrate

# Create superuser/admin
python manage.py createsuperuser
```

### 6. Run the server
```bash
python manage.py runserver
```
