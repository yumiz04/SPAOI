import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { ChatView } from './components/chat/ChatView';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<ChatView />} path="/" />
        <Route element={<Navigate replace to="/" />} path="*" />
      </Routes>
    </BrowserRouter>
  );
}

export default App;