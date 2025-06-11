# Настройка BitBucket репозитория

## 🔧 Шаги для настройки BitBucket

### 1. Создание репозитория на BitBucket
1. Перейдите на [bitbucket.org](https://bitbucket.org/)
2. Войдите в свой аккаунт или создайте новый
3. Нажмите "Create repository"
4. Укажите название: `rag-stroyactiv-pyton`
5. Сделайте репозиторий приватным или публичным по желанию
6. Создайте репозиторий

### 2. Настройка аутентификации

#### Вариант A: SSH ключи (рекомендуется)
```bash
# Генерируем SSH ключ (если его нет)
ssh-keygen -t ed25519 -C "your-email@example.com"

# Копируем публичный ключ
cat ~/.ssh/id_ed25519.pub

# Добавляем ключ в BitBucket:
# Settings → SSH Keys → Add Key
```

#### Вариант B: App Password
```bash
# Создайте App Password в BitBucket:
# Settings → App passwords → Create app password
# Права: Repositories (Read, Write)

# Обновите URL с учетными данными:
git remote set-url bitbucket https://USERNAME:APP_PASSWORD@bitbucket.org/USERNAME/rag-stroyactiv-pyton.git
```

### 3. Обновление URL репозитория
```bash
# Замените USERNAME на ваш логин BitBucket
git remote set-url bitbucket https://bitbucket.org/USERNAME/rag-stroyactiv-pyton.git

# Или для SSH:
git remote set-url bitbucket git@bitbucket.org:USERNAME/rag-stroyactiv-pyton.git
```

### 4. Первая отправка
```bash
# Отправляем весь репозиторий в BitBucket
git push bitbucket main
```

## 🚀 Использование скрипта синхронизации

После настройки BitBucket, используйте скрипт для автоматической синхронизации:

```bash
./sync_repos.sh
```

Этот скрипт:
- Проверит изменения
- Создаст коммит (если нужно)
- Отправит изменения в GitHub
- Отправит изменения в BitBucket

## 📝 Полезные команды

```bash
# Проверить настроенные репозитории
git remote -v

# Отправить только в GitHub
git push origin main

# Отправить только в BitBucket
git push bitbucket main

# Отправить во все репозитории одновременно
git remote | xargs -L1 git push --all
``` 