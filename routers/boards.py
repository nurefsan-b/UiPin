# routers/boards.py
from fastapi import APIRouter, Depends, Request, Form, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, insert
from sqlalchemy.orm import selectinload
from starlette.templating import Jinja2Templates
from typing import Annotated

from database import get_db
from models import Board, User, Pin, board_pins, Comment 

router = APIRouter(
    tags=["Boards"],
    include_in_schema=False
)

templates = Jinja2Templates(directory="templates")

#Otomatik Pano Kontrolü 
async def ensure_default_board(db: AsyncSession, user_id: int):
    """Kullanıcının 'Kaydedilenler' panosu yoksa oluşturur."""
    result = await db.execute(
        select(Board).where(Board.owner_id == user_id, Board.title == "Kaydedilenler")
    )
    default_board = result.scalars().first()
    
    if not default_board:
        new_board = Board(
            title="Kaydedilenler",
            description="Varsayılan kayıt panosu",
            owner_id=user_id,
            cover_image="images/default_board.jpg" 
        )
        db.add(new_board)
        await db.commit()
        await db.refresh(new_board)
        return new_board
    return default_board

#1. PANOLARI LİSTELE (SAYFA)
@router.get("/boards")
async def show_boards_page(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id") or request.cookies.get("user_id")
    if not user_id:
        return templates.TemplateResponse("boards.html", {"request": request, "user": None, "boards": []})

    user_id = int(user_id)

    # 1. Otomatik Panoyu Garantiye Al
    await ensure_default_board(db, user_id)

    # 2. Tüm Panoları Çek
    result = await db.execute(
        select(Board)
        .where(Board.owner_id == user_id)
        .options(selectinload(Board.pins))
        .order_by(Board.created_at.desc())
    )
    boards = result.scalars().all()

    for b in boards:
        b.pin_count = len(b.pins)

    user_result = await db.execute(select(User).where(User.id == user_id))
    current_user = user_result.scalars().first()

    return templates.TemplateResponse("boards.html", {
        "request": request, 
        "boards": boards, 
        "user": current_user, 
        "current_user": current_user,
        "active_page": "boards"
    })

#2. YENİ PANO OLUŞTUR (POST)
@router.post("/create/board")
async def create_board(
    request: Request,
    title: Annotated[str, Form()],
    description: Annotated[str, Form()] = "",
    is_secret: Annotated[bool, Form()] = False, 
    db: AsyncSession = Depends(get_db)
):
    user_id = request.session.get("user_id") or request.cookies.get("user_id")
    if not user_id:
        return templates.TemplateResponse("login.html", {"request": request})
    
    new_board = Board(
        title=title,
        description=description,
        is_secret=is_secret,
        owner_id=int(user_id),
        cover_image="images/default_board.jpg"
    )
    db.add(new_board)
    await db.commit()
    
    return await show_boards_page(request, db)

#3.PANO DETAYI 
@router.get("/board/{board_id}")
async def get_board_detail(board_id: int, request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id") or request.cookies.get("user_id")
    
    result = await db.execute(
        select(Board)
        .where(Board.id == board_id)
        .options(
            selectinload(Board.pins).selectinload(Pin.snippets), # Pinlerin kod parçaları
            selectinload(Board.pins).selectinload(Pin.comments).selectinload(Comment.user), # Yorumlar
            selectinload(Board.pins).selectinload(Pin.owner) # Pin sahibi
        )
    )
    board = result.scalars().first()
    
    if not board:
        return "Pano bulunamadı"

    current_user = None
    if user_id:
        u_res = await db.execute(select(User).where(User.id == int(user_id)))
        current_user = u_res.scalars().first()
    active_pins = [p for p in board.pins if not p.is_deleted]
    return templates.TemplateResponse("board_detail.html", {
        "request": request,
        "board": board,
        "pins": active_pins,
        "user": current_user,
        "current_user": current_user
    })

#5. JSON API: KULLANICININ PANOLARINI GETİR 
@router.get("/boards/api/user_boards")
async def get_user_boards_json(request: Request, db: AsyncSession = Depends(get_db)):
    user_id = request.session.get("user_id") or request.cookies.get("user_id")
    if not user_id:
        return [] 
    
    await ensure_default_board(db, int(user_id))
    
    result = await db.execute(
        select(Board)
        .where(Board.owner_id == int(user_id))
        .order_by(Board.created_at.desc())
    )
    boards = result.scalars().all()

    return [{"id": b.id, "title": b.title, "cover": b.cover_image} for b in boards]