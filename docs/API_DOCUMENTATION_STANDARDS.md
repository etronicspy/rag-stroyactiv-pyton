# API Documentation Standards

## General Swagger Documentation Principles

### 1. Summary and response_description Structure

**Summary format:**
```
🩺 [Name] – [Brief description in English]
```

**Examples:**
- `🩺 Basic Health Check – Quick Service Status`
- `🔍 Full Health Check – Comprehensive System Diagnostics`
- `📦 Batch Processing – Batch Materials Processing`

### 2. Docstring Structure

**Required sections:**
```python
"""
[Emoji] **[Name]** - [Description in English]

[Detailed functionality description]

**Features:**
- [Emoji] [Feature description]
- [Emoji] [Feature description]

**Response Example:**
```json
{
    // Response example
}
```

**Response Status Codes:**
- **200 OK**: [Description in English]
- **500 Internal Server Error**: [Description in English]

**Use Cases:**
- [Use case description]
- [Use case description]
"""
```

### 3. Health Endpoints Standards

#### Basic Health Check
```python
@router.get(
    "",
    summary="🩺 Basic Health Check – Quick Service Status",
    response_description="Essential service health information and uptime"
)
```

#### Full Health Check
```python
@router.get(
    "/full",
    summary="🔍 Full Health Check – Comprehensive System Diagnostics",
    response_description="Complete health diagnostics with database and service status"
)
```

#### Service-Specific Health
```python
@router.get(
    "/health",
    summary="🩺 [Service Name] Health – [Service] Service Status",
    response_description="[Service] service health information"
)
```

### 4. Standards for Other Endpoints

#### CRUD Operations
```python
@router.post(
    "/",
    summary="➕ Create [Entity] – Create [entity]",
    response_description="Created [entity]"
)

@router.get(
    "/{id}",
    summary="🔍 Get [Entity] – Get [entity] by ID",
    response_description="[Entity] data"
)

@router.put(
    "/{id}",
    summary="✏️ Update [Entity] – Update [entity]",
    response_description="Updated [entity]"
)

@router.delete(
    "/{id}",
    summary="🗑️ Delete [Entity] – Delete [entity]",
    response_description="Deletion result"
)
```

#### Special Operations
```python
@router.post(
    "/batch",
    summary="📦 Batch [Operation] – Batch [operation]",
    response_description="Batch [operation] results"
)

@router.post(
    "/import",
    summary="📥 Import [Entity] – Import [entities]",
    response_description="Import [entities] result"
)

@router.get(
    "/search",
    summary="🔍 Search [Entity] – Search [entities]",
    response_description="Search [entities] results"
)
```

### 5. Эмодзи для различных типов операций

- 🩺 Health checks
- 🔍 Search/Get operations
- ➕ Create operations
- ✏️ Update operations
- 🗑️ Delete operations
- 📦 Batch operations
- 📥 Import operations
- 📤 Upload operations
- 📊 Statistics/Metrics
- 🔄 Retry/Restart operations
- 🧹 Cleanup operations
- ⚙️ Configuration operations
- ▶️ Start operations
- ⏹️ Stop operations
- 🔌 Status operations

### 6. Language Standards

- **summary**: English language with emojis
- **response_description**: English language
- **docstring**: English language for descriptions
- **Status codes**: English language
- **Use cases**: English language

### 7. Response Examples

All examples should be:
- Realistic
- Complete
- With English comments
- With data type specifications

### 8. Error Response Standards

```python
responses={
    400: {"description": "Data validation error"},
    404: {"description": "[Entity] not found"},
    500: {"description": "Internal server error"},
    503: {"description": "Service temporarily unavailable"}
}
```

## Standards Application

1. **All new endpoints** must follow these standards
2. **Existing endpoints** are gradually updated during refactoring
3. **Health endpoints** should be updated first
4. **Documentation** must be current and complete

## Compliance Checking

To check compliance with standards use:
```bash
# Check health endpoints
grep -r "summary.*Health" api/routes/

# Check emojis in summary
grep -r "summary.*🩺\|summary.*🔍\|summary.*➕" api/routes/
``` 