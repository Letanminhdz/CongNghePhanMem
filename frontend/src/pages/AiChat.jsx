import React, { useState, useRef, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { ChatService } from '../client';
import { useUser } from '../context/UserContext';

const WELCOME_MSG = {
  id: 'welcome',
  role: 'ai',
  text: "Hello! I'm your medical AI assistant. I can help you learn about symptoms, medications, or check drug interactions.",
  suggestions: ['Ibuprofen side effects', 'What is hypertension?', 'Check drug interactions'],
};

const AiChat = () => {
  const { user } = useUser(); // user: Thông tin người dùng hiện tại lấy từ Context
  const [messages, setMessages] = useState([WELCOME_MSG]); // messages: Danh sách các tin nhắn hiển thị trong màn hình chat (bao gồm tin nhắn của user và ai)
  const [chatHistory, setChatHistory] = useState([]); // chatHistory: Danh sách lịch sử các cuộc hội thoại lấy từ API
  const [input, setInput] = useState(''); // input: Dữ liệu nhập vào của ô chat từ người dùng
  const [sending, setSending] = useState(false); // sending: Trạng thái đang gửi tin nhắn lên server để khóa input/nút bấm
  const [loadingHistory, setLoadingHistory] = useState(true); // loadingHistory: Trạng thái đang tải lịch sử chat từ backend
  const bottomRef = useRef(null); // bottomRef: Tham chiếu tới phần tử cuối danh sách tin nhắn để tự động cuộn xuống khi có tin nhắn mới
  const location = useLocation();
  const initialSentRef = useRef(false);

  // Effect: Tự động tải lịch sử chat từ API backend khi Component được mount
  useEffect(() => {
    const fetchHistory = async () => {
      try {
        // data: Lấy dữ liệu 20 cuộc hội thoại gần nhất của người dùng từ API
        const data = await ChatService.getChatHistoryApiV1ChatHistoryGet({ limit: 20 });
        setChatHistory(data?.items || []);

        // Khôi phục phiên chat trước đó nếu có lịch sử trò chuyện
        if (data?.items?.length > 0) {
          const restored = []; // restored: Mảng lưu trữ tin nhắn được phục dựng từ lịch sử
          data.items.slice().reverse().forEach(item => {
            restored.push({ id: `u-${item.id}`, role: 'user', text: item.message });
            restored.push({
              id: `a-${item.id}`,
              role: 'ai',
              text: item.response,
              intent: item.intent,
            });
          });
          setMessages([WELCOME_MSG, ...restored]);
        }
      } catch (err) {
        console.error('Failed to load chat history', err);
      } finally {
        setLoadingHistory(false);
      }
    };
    fetchHistory();
  }, []);

  // Effect: Tự động cuộn xuống cuối màn hình chat mỗi khi danh sách tin nhắn thay đổi
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Effect: Tự động gửi câu hỏi nếu có truyền từ trang khác (như Medicine/Disease Detail)
  useEffect(() => {
    if (!loadingHistory && location.state?.q && !initialSentRef.current) {
      initialSentRef.current = true;
      sendMessage(location.state.q);
      // Xoá state để không gửi lại nếu user F5 trang
      window.history.replaceState({}, document.title);
    }
  }, [loadingHistory, location.state]);

  // sendMessage: Hàm xử lý gửi tin nhắn lên API và nhận phản hồi RAG
  const sendMessage = async (text) => {
    const msgText = typeof text === 'string' ? text : input; // msgText: Văn bản tin nhắn thực tế cần gửi (ưu tiên tham số truyền vào hoặc dùng input state)
    if (!msgText.trim() || sending) return;

    const userMsg = { id: Date.now(), role: 'user', text: msgText }; // userMsg: Đối tượng tin nhắn của người dùng để cập nhật lên UI
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setSending(true);

    // Hiển thị trạng thái AI đang gõ chữ (typing indicator)
    const typingId = Date.now() + 0.5; // typingId: ID tạm thời cho tin nhắn đang chờ phản hồi
    setMessages(prev => [...prev, { id: typingId, role: 'ai', typing: true }]);

    try {
      // response: Kết quả trả về từ API chatbot y khoa bao gồm câu trả lời, nguồn và các cảnh báo
      const response = await ChatService.askQuestionApiV1ChatAskPost({
        requestBody: {
          message: msgText
        }
      });
      setMessages(prev => prev.filter(m => m.id !== typingId)); // Xóa biểu tượng đang gõ sau khi nhận phản hồi
      const aiReply = {
        id: Date.now() + 1,
        role: 'ai',
        text: response.answer,
        sources: response.sources || [],
        warnings: response.warnings || [],
        entities: response.entities || [],
      }; // aiReply: Đối tượng phản hồi hoàn chỉnh của AI trợ lý
      setMessages(prev => [...prev, aiReply]);
      
      // Làm mới danh sách lịch sử chat ở sidebar
      ChatService.getChatHistoryApiV1ChatHistoryGet({ limit: 20 })
        .then(d => setChatHistory(d?.items || []))
        .catch(() => {});
    } catch (err) {
      setMessages(prev => prev.filter(m => m.id !== typingId)); // Xóa biểu tượng đang gõ khi xảy ra lỗi
      setMessages(prev => [...prev, {
        id: Date.now() + 1,
        role: 'ai',
        text: "Sorry, I'm having trouble connecting to the server. Please try again.",
      }]);
    } finally {
      setSending(false);
    }
  };

  // handleKey: Hàm xử lý sự kiện bấm phím trong ô nhập liệu (bấm Enter để gửi, Shift+Enter để xuống dòng)
  const handleKey = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  // initials: Chữ cái viết tắt tên người dùng hiển thị làm Avatar
  const initials = user?.full_name
    ? user.full_name.split(' ').map(n => n[0]).join('').toUpperCase().slice(0, 2)
    : 'U';



  return (
    <div className="flex flex-row h-[calc(100vh-4rem)]">
      {/* Main chat area */}
      <div className="flex-1 flex flex-col bg-background min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 md:p-8 flex flex-col gap-6">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex gap-4 max-w-3xl mx-auto w-full ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
              {msg.role === 'ai' ? (
                <div className="w-8 h-8 rounded-full bg-primary flex-shrink-0 flex items-center justify-center text-primary-foreground">
                  <iconify-icon icon="lucide:bot" class="text-lg"></iconify-icon>
                </div>
              ) : (
                <div className="w-8 h-8 rounded-full bg-primary/10 border border-border flex-shrink-0 flex items-center justify-center text-primary text-sm font-bold">
                  {initials}
                </div>
              )}

              <div className={`flex-1 ${msg.role === 'user' ? 'flex flex-col items-end' : 'space-y-2'}`}>
                <p className="text-sm font-medium text-foreground mb-1">
                  {msg.role === 'ai' ? 'MediAI Assistant' : (user?.full_name || 'You')}
                </p>

                {msg.typing ? (
                  <div className="flex items-center gap-4 px-6 py-4 bg-secondary/60 rounded-2xl rounded-tl-sm w-fit animate-pulse border border-border/50 shadow-sm">
                    <iconify-icon icon="lucide:sparkles" class="text-primary text-xl animate-spin-slow"></iconify-icon>
                    <span className="text-sm font-medium text-muted-foreground">MediAI is thinking...</span>
                    <div className="flex gap-1.5 ml-2">
                      <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
                      <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
                      <span className="w-1.5 h-1.5 bg-primary rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
                    </div>
                  </div>
                ) : msg.role === 'user' ? (
                  <div className="bg-primary text-primary-foreground px-5 py-3 rounded-2xl rounded-tr-sm text-base leading-relaxed max-w-[85%]">
                    {msg.text}
                  </div>
                ) : (
                  <div className="text-base text-foreground leading-relaxed whitespace-pre-wrap">
                    {msg.text}
                  </div>
                )}

                {/* Warnings */}
                {msg.warnings?.length > 0 && (
                  <div className="bg-amber-50 border border-amber-200 rounded-xl p-4 flex gap-3 mt-2">
                    <iconify-icon icon="lucide:triangle-alert" class="text-amber-600 text-xl flex-shrink-0 mt-0.5"></iconify-icon>
                    <div>
                      {msg.warnings.map((w, i) => (
                        <p key={i} className="text-sm text-amber-800">{w}</p>
                      ))}
                    </div>
                  </div>
                )}

                {/* Suggestions */}
                {msg.suggestions && (
                  <div className="flex flex-wrap gap-2 mt-4">
                    {msg.suggestions.map((s) => (
                      <button key={s} onClick={() => sendMessage(s)} className="px-3 py-1.5 bg-secondary text-muted-foreground hover:text-foreground hover:bg-secondary/80 rounded-full text-xs font-medium border border-border transition-colors">
                        {s}
                      </button>
                    ))}
                  </div>
                )}

                {/* Sources */}
                {msg.sources?.length > 0 && (
                  <div className="flex items-center gap-2 mt-4 pt-4 border-t border-border">
                    <span className="text-xs font-medium text-muted-foreground">Sources:</span>
                    {msg.sources.map((src) => (
                      <span key={src} className="px-2 py-1 bg-secondary rounded text-[10px] font-medium text-muted-foreground flex items-center gap-1">
                        <iconify-icon icon="lucide:link"></iconify-icon> {src}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>

        {/* Input area */}
        <div className="shrink-0 bg-background border-t border-border/50 pt-4 pb-6 px-4 md:px-8">
          <div className="max-w-3xl mx-auto w-full relative">
            <div className="bg-card border border-border rounded-3xl p-2 shadow-lg flex items-end gap-2 focus-within:ring-2 focus-within:ring-primary/20 focus-within:border-primary transition-all">
              <textarea
                rows={1}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKey}
                disabled={sending}
                placeholder="Ask about symptoms, medications, or drug interactions..."
                className="w-full max-h-32 bg-transparent border-none focus:ring-0 resize-none py-3 px-2 text-sm text-foreground placeholder:text-muted-foreground outline-none disabled:opacity-50"
                style={{ minHeight: '44px' }}
              />
              <button
                onClick={() => sendMessage()}
                disabled={sending || !input.trim()}
                className="p-2.5 bg-primary text-primary-foreground rounded-full hover:bg-primary/90 transition-colors flex-shrink-0 shadow-sm disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <iconify-icon icon={sending ? 'lucide:loader-circle' : 'lucide:send'} class="text-xl"></iconify-icon>
              </button>
            </div>
            <div className="text-center mt-3">
              <p className="text-[10px] text-muted-foreground">MediAI may make mistakes. Always verify important medical information with a healthcare professional.</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AiChat;
