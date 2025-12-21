# models.py
from sqlalchemy import Column, Integer, String, Text, DateTime, func, Boolean, ForeignKey, Table
from sqlalchemy.orm import relationship
from database import Base 

# =================================================================
# ARA TABLOLAR (M2M İlişkileri)
# =================================================================

# 1. Pano-Pin İlişkisi (Hangi pin hangi panoda?)
board_pins = Table(
    'board_pins', Base.metadata,
    Column('board_id', Integer, ForeignKey('boards.id')),
    Column('pin_id', Integer, ForeignKey('pins.id'))
)

# 2. Beğeni İlişkisi (Hangi Kullanıcı Hangi Pini Beğendi?)
pin_likes = Table(
    'pin_likes', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('pin_id', Integer, ForeignKey('pins.id'), primary_key=True)
)

# =================================================================
# ANA MODELLER
# =================================================================

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Profil Bilgileri
    profile_picture = Column(String, nullable=True) 
    first_name = Column(String(50), nullable=True) 
    last_name = Column(String(50), nullable=True)
    gender = Column(String(50), nullable=True) 
    age = Column(Integer, nullable=True) 
    is_superuser = Column(Boolean, default=False) 

    # İlişkiler (One-to-Many)
    pins = relationship("Pin", back_populates="owner") 
    boards = relationship("Board", back_populates="owner")
    comments = relationship("Comment", back_populates="user")
    
    # İlişkiler (Many-to-Many)
    liked_pins = relationship("Pin", secondary=pin_likes, back_populates="liked_by_users")
    
    # Mesajlaşma ilişkileri (Message tablosundaki backref'lerden gelir: sent_messages, received_messages)
    # Bildirim ilişkileri (Notification tablosundaki backref'ten gelir: notifications)

    def __repr__(self):
        return f"<User(username='{self.username}')>"

class Board(Base):
    """Kullanıcıların Panoları"""
    __tablename__ = "boards"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    cover_image = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_secret = Column(Boolean, default=False)
    owner_id = Column(Integer, ForeignKey("users.id"))
    owner = relationship("User", back_populates="boards")
    
    pins = relationship("Pin", secondary=board_pins, backref="saved_in_boards")

class Comment(Base):
    """Pinlere yapılan yorumlar"""
    __tablename__ = "comments"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    user_id = Column(Integer, ForeignKey("users.id"))
    user = relationship("User", back_populates="comments")
    
    pin_id = Column(Integer, ForeignKey("pins.id"))
    pin = relationship("Pin", back_populates="comments")

class CodeSnippet(Base):
    __tablename__ = "code_snippets"
    
    id = Column(Integer, primary_key=True, index=True)
    language = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    
    pin_id = Column(Integer, ForeignKey("pins.id"))
    pin = relationship("Pin", back_populates="snippets")

class Pin(Base):
    __tablename__ = "pins"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(100), index=True)
    description = Column(Text, nullable=True)
    image_path = Column(String, unique=True, index=True) 
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    tag = Column(String(50), index=True, nullable=True) # Hata almamak için nullable=True yaptım
    like_count = Column(Integer, default=0)
    is_deleted = Column(Boolean, default=False)

    # Foreign Key ve Owner İlişkisi
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="pins")

    # İlişkiler
    comments = relationship("Comment", back_populates="pin")
    snippets = relationship("CodeSnippet", back_populates="pin")
    liked_by_users = relationship("User", secondary=pin_likes, back_populates="liked_pins")

class Message(Base):
    """Kullanıcılar arasındaki birebir mesajlaşmayı tutar."""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    content = Column(Text, nullable=False)
    
    # Gönderen ve Alan Kişi
    sender_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    receiver_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False)
    
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # İlişkiler
    sender = relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    receiver = relationship("User", foreign_keys=[receiver_id], backref="received_messages")

    def __repr__(self):
        return f"<Message(id={self.id}, sender={self.sender_id}, receiver={self.receiver_id})>"

class Notification(Base):
    """Kullanıcı bildirimleri (Beğeni, Yorum vb.)"""
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, index=True)
    
    recipient_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False) # Bildirimi alan
    actor_id = Column(Integer, ForeignKey("users.id"), nullable=False) # Bildirimi yapan
    
    verb = Column(String, nullable=False) # "liked", "commented"
    pin_id = Column(Integer, ForeignKey("pins.id"), nullable=True) # Hangi pin?
    
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # İlişkiler
    recipient = relationship("User", foreign_keys=[recipient_id], backref="notifications")
    actor = relationship("User", foreign_keys=[actor_id])
    pin = relationship("Pin")

class Report(Base):
    """Kullanıcıların pinleri şikayet etmesi için tablo"""
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True, index=True)
    reason = Column(String(50), nullable=False) # Spam, Şiddet vb.
    status = Column(String(20), default="pending") # pending, resolved, dismissed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    pin_id = Column(Integer, ForeignKey("pins.id"), nullable=False)
    
    # İlişkiler
    reporter = relationship("User", foreign_keys=[reporter_id])
    pin = relationship("Pin")