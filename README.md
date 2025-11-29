# Find Dee - Smart Student Assistant 🎓

Find Dee is a LINE Chatbot and Mini App designed to help students manage their files and academic schedules efficiently. It integrates seamlessly with LINE to provide a convenient way to store files, track assignments, and stay organized.

## 🚀 Features

### 🤖 LINE Chatbot
- **File Saver**: Automatically saves files (PDFs, Images) sent to the chat to Firebase Storage.
- **Smart Tagging**: Uses Gen AI to automatically tag and categorize uploaded files (e.g., "Lecture Notes", "Homework").
- **Quick Access**: Retrieve files directly through chat commands.

### 📱 LINE Mini App
- **File Dashboard**: A visual interface to browse, search, and manage your saved files.
- **Smart Planner**: A calendar view to manage assignments and due dates.
    - **Create/Edit Tasks**: Add tasks with subjects, due dates, and custom tags.
    - **Real-time Updates**: Tasks are synced in real-time across devices.
    - **Task Tracking**: Mark tasks as complete and visualize your progress.
- **Group Collaboration**: Shared file access for study groups (files uploaded in a group are accessible to members).

## 🛠️ Tech Stack

- **Frontend**: React (Vite), Bootstrap, Lucide React, LINE LIFF SDK
- **Backend**: Python (FastAPI), Firebase Admin SDK
- **Database**: Firebase Realtime Database
- **Storage**: Firebase Storage
- **Infrastructure**: Ngrok (for local tunneling)

## ⚙️ Setup Instructions

### Prerequisites
- Node.js (v18+)
- Python (v3.9+)
- Firebase Project (with Realtime Database and Storage enabled)
- LINE Developers Channel (Messaging API & LIFF)

### 1. Backend Setup
```bash
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```
- Place your `serviceAccountKey.json` from Firebase in the `backend/` directory.
- Create a `.env` file with your LINE Channel credentials:
```env
LINE_CHANNEL_ACCESS_TOKEN=your_token
LINE_CHANNEL_SECRET=your_secret
```
- Run the server:
```bash
uvicorn main:app --reload --port 8001
```

For detailed backend documentation, see [backend/README.md](backend/README.md).

### 2. Frontend Setup
```bash
cd frontend
npm install
```
- Create a `.env` file:
```env
VITE_LIFF_ID=your_liff_id
VITE_API_URL=https://your-backend-url.ngrok-free.app
```
- Run the development server:
```bash
npm run dev
```

## 📝 Usage

1. **Add the Bot**: Add the Find Dee bot to your LINE friends or a study group.
2. **Upload Files**: Send a file to the chat. The bot will acknowledge and save it.
3. **Open Mini App**: Click the rich menu or link to open the Mini App.
4. **Manage Tasks**: Use the Planner tab to add homework and exam dates.

## 👥 Team
- **Sittipon** - Developer
# Find-Dee
