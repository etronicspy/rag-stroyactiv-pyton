#!/bin/bash

# Скрипт для синхронизации с GitHub и BitBucket репозиториями

echo "🚀 Синхронизация с удаленными репозиториями..."

# Проверяем статус git
echo "📋 Статус репозитория:"
git status --porcelain

# Если есть изменения, добавляем их
if [[ -n $(git status --porcelain) ]]; then
    echo "📝 Добавляем изменения..."
    git add .
    
    # Запрашиваем сообщение коммита
    echo "💬 Введите сообщение коммита:"
    read -r commit_message
    
    if [[ -z "$commit_message" ]]; then
        commit_message="feat: Auto-sync changes $(date '+%Y-%m-%d %H:%M:%S')"
    fi
    
    echo "✅ Создаем коммит: $commit_message"
    git commit -m "$commit_message"
fi

# Пушим в GitHub
echo "🐙 Отправляем в GitHub..."
if git push origin main; then
    echo "✅ GitHub: успешно обновлен"
else
    echo "❌ GitHub: ошибка при отправке"
fi

# Пушим в BitBucket
echo "🗂️  Отправляем в BitBucket..."
if git push bitbucket main; then
    echo "✅ BitBucket: успешно обновлен"
else
    echo "❌ BitBucket: ошибка при отправке (возможно нужна настройка аутентификации)"
    echo "🔧 Для настройки BitBucket:"
    echo "   1. Создайте репозиторий на https://bitbucket.org/"
    echo "   2. Настройте SSH ключи или App passwords"
    echo "   3. Обновите URL: git remote set-url bitbucket YOUR_BITBUCKET_URL"
fi

echo "🎉 Синхронизация завершена!" 