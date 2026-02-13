---
name: security-review
description: Use this skill when implementing authentication, handling user input, working with secrets, creating API endpoints, or building payment/sensitive features. Provides comprehensive security checklist and patterns.
---

# Security Review Skill

This skill ensures all code follows security best practices and helps identify potential vulnerabilities.

## When to Activate

- Implementing authentication or authorization
- Handling user input or file uploads
- Creating new API endpoints
- Working with secrets or credentials
- Implementing payment features
- Storing or transmitting sensitive data
- Integrating third-party APIs

## Security Checklist

### 1. Secrets Management

#### ❌ NEVER Do This
```typescript
const apiKey = "sk-proj-xxxxx"  // Hardcoded secret
const dbPassword = "password123" // In source code
```

#### ✅ ALWAYS Do This
```typescript
const apiKey = process.env.OPENAI_API_KEY
const dbUrl = process.env.DATABASE_URL

// Verify secrets exist at startup
if (!apiKey) {
  throw new Error('OPENAI_API_KEY not configured')
}
```

#### Verification Steps
- [ ] No hardcoded API keys, tokens, or passwords
- [ ] All secrets in environment variables
- [ ] `.env.local` and `.env` in .gitignore
- [ ] No secrets in git history (check with `git log -p`)
- [ ] Production secrets in hosting platform (Vercel, DO, Railway)

---

### 2. Input Validation

#### Always Validate User Input (Server-Side)

```typescript
import { z } from 'zod'

// Define validation schema
const CreateUserSchema = z.object({
  email: z.string().email(),
  name: z.string().min(1).max(100),
  age: z.number().int().min(0).max(150).optional()
})

// Validate before processing
export async function createUser(input: unknown) {
  const validated = CreateUserSchema.parse(input)
  return await db.users.create(validated)
}
```

#### File Upload Validation

```typescript
function validateFileUpload(file: File) {
  // Size check (5MB max)
  const maxSize = 5 * 1024 * 1024
  if (file.size > maxSize) {
    throw new Error('File too large (max 5MB)')
  }

  // Type allowlist (not blocklist)
  const allowedTypes = ['image/jpeg', 'image/png', 'image/gif']
  if (!allowedTypes.includes(file.type)) {
    throw new Error('Invalid file type')
  }

  return true
}
```

#### Verification Steps
- [ ] All user inputs validated on server-side (client validation is not enough)
- [ ] File uploads restricted (size, type, extension)
- [ ] No direct use of user input in queries/commands
- [ ] Allowlist validation (not blocklist)
- [ ] Error messages don't leak sensitive info

---

### 3. SQL/NoSQL Injection Prevention

#### ❌ NEVER Concatenate User Input
```typescript
// DANGEROUS - SQL Injection vulnerability
const query = `SELECT * FROM users WHERE email = '${userEmail}'`
await db.query(query)
```

#### ✅ ALWAYS Use Parameterized Queries
```typescript
// Django ORM
User.objects.filter(email=user_email)

// Raw SQL with parameters
cursor.execute("SELECT * FROM users WHERE email = %s", [user_email])

// Prisma
await prisma.user.findUnique({ where: { email: userEmail } })
```

#### Verification Steps
- [ ] All database queries use ORM or parameterized queries
- [ ] No string concatenation/interpolation in SQL
- [ ] Query builders used correctly

---

### 4. Authentication & Authorization

#### Token Storage
```typescript
// ❌ WRONG: localStorage (vulnerable to XSS)
localStorage.setItem('token', token)

// ✅ CORRECT: httpOnly cookies (for session tokens)
res.setHeader('Set-Cookie',
  `session=${token}; HttpOnly; Secure; SameSite=Strict; Max-Age=3600`)
```

#### Authorization Checks
```typescript
export async function deleteResource(resourceId: string, userId: string) {
  // ALWAYS verify authorization
  const resource = await db.resources.findUnique({ where: { id: resourceId } })

  if (resource.ownerId !== userId) {
    return { error: 'Unauthorized', status: 403 }
  }

  // Proceed with deletion
  await db.resources.delete({ where: { id: resourceId } })
}
```

#### Verification Steps
- [ ] Session tokens in httpOnly cookies (not localStorage)
- [ ] Authorization checks before every sensitive operation
- [ ] Role-based access control implemented
- [ ] No IDOR (Insecure Direct Object Reference) - always verify ownership

---

### 5. XSS Prevention

#### Sanitize User-Provided HTML
```typescript
import DOMPurify from 'isomorphic-dompurify'

// ALWAYS sanitize before rendering user HTML
function renderUserContent(html: string) {
  const clean = DOMPurify.sanitize(html, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br'],
    ALLOWED_ATTR: []
  })
  return <div dangerouslySetInnerHTML={{ __html: clean }} />
}
```

#### React's Built-in Protection
```tsx
// ✅ SAFE: React escapes by default
<div>{userInput}</div>

// ⚠️ DANGEROUS: Bypasses React's protection
<div dangerouslySetInnerHTML={{ __html: userInput }} />
```

#### Verification Steps
- [ ] User-provided HTML sanitized with DOMPurify
- [ ] `dangerouslySetInnerHTML` only used with trusted/sanitized content
- [ ] CSP headers configured
- [ ] No unvalidated dynamic content rendering

---

### 6. CSRF Protection

#### SameSite Cookies
```typescript
res.setHeader('Set-Cookie',
  `session=${sessionId}; HttpOnly; Secure; SameSite=Strict`)
```

#### CSRF Tokens for Forms
```typescript
// Verify token on state-changing requests
export async function POST(request: Request) {
  const csrfToken = request.headers.get('X-CSRF-Token')

  if (!verifyCSRFToken(csrfToken)) {
    return new Response('Invalid CSRF token', { status: 403 })
  }

  // Process request
}
```

#### Verification Steps
- [ ] SameSite=Strict or Lax on session cookies
- [ ] CSRF tokens on state-changing operations (POST, PUT, DELETE)
- [ ] Token validation on server-side

---

### 7. Rate Limiting

#### API Rate Limiting
```typescript
// Example with express-rate-limit
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // 100 requests per window
  message: 'Too many requests'
})

// Stricter for auth endpoints
const authLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: 'Too many login attempts'
})
```

#### Verification Steps
- [ ] Rate limiting on all API endpoints
- [ ] Stricter limits on login/auth endpoints
- [ ] Stricter limits on expensive operations (search, AI calls)

---

### 8. Sensitive Data Exposure

#### Logging
```python
# ❌ WRONG: Logging sensitive data
logger.info(f"User login: {email}, password: {password}")

# ✅ CORRECT: Redact sensitive data
logger.info(f"User login: {email}, user_id: {user_id}")
```

#### Error Responses
```typescript
// ❌ WRONG: Exposing internal details
catch (error) {
  return { error: error.message, stack: error.stack }
}

// ✅ CORRECT: Generic error for users
catch (error) {
  console.error('Internal error:', error)  // Log full error server-side
  return { error: 'An error occurred. Please try again.' }
}
```

#### Verification Steps
- [ ] No passwords, tokens, or secrets in logs
- [ ] Error messages generic for users (detailed only in server logs)
- [ ] No stack traces exposed to users
- [ ] PII handled according to privacy policy

---

### 9. Dependency Security

#### Regular Updates
```bash
# Check for vulnerabilities
npm audit
pip-audit

# Fix automatically fixable issues
npm audit fix

# Check for outdated packages
npm outdated
pip list --outdated
```

#### Lock Files
```bash
# ALWAYS commit lock files
git add package-lock.json  # or pnpm-lock.yaml, Pipfile.lock

# Use in CI/CD for reproducible builds
npm ci  # Instead of npm install
```

#### Verification Steps
- [ ] Dependencies up to date
- [ ] No known vulnerabilities (`npm audit` / `pip-audit` clean)
- [ ] Lock files committed to repo
- [ ] Dependabot or similar enabled

---

## Security Headers Checklist

For production deployments:

```
Content-Security-Policy: default-src 'self'; script-src 'self'
Strict-Transport-Security: max-age=31536000; includeSubDomains
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: strict-origin-when-cross-origin
Permissions-Policy: geolocation=(), camera=(), microphone=()
```

---

## Pre-Deployment Security Checklist

Before ANY production deployment:

- [ ] **Secrets**: No hardcoded secrets, all in env vars
- [ ] **Input Validation**: All user inputs validated server-side
- [ ] **Injection**: All queries parameterized
- [ ] **XSS**: User content sanitized
- [ ] **CSRF**: Protection enabled
- [ ] **Authentication**: Proper token handling
- [ ] **Authorization**: Role/ownership checks in place
- [ ] **Rate Limiting**: Enabled on sensitive endpoints
- [ ] **HTTPS**: Enforced in production
- [ ] **Security Headers**: CSP, HSTS, X-Frame-Options set
- [ ] **Error Handling**: No sensitive data in errors
- [ ] **Logging**: No sensitive data logged
- [ ] **Dependencies**: Up to date, no vulnerabilities
- [ ] **File Uploads**: Size, type validated

---

## Resources

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [OWASP Cheat Sheets](https://cheatsheetseries.owasp.org/)
- [Django Security](https://docs.djangoproject.com/en/stable/topics/security/)
- [Next.js Security](https://nextjs.org/docs/security)

---

**Remember**: Security is not optional. One vulnerability can compromise the entire platform and user data. When in doubt, err on the side of caution.
