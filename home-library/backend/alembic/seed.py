"""
Seed data 脚本
创建测试数据
"""
import sys
sys.path.insert(0, "..")

from sqlalchemy.orm import Session
from app.db.database import sync_engine, Base
from app.models.models import (
    Work, Edition, Book, Bookshelf, Shelf, ShelfPosition,
    Category, Tag
)


def create_seed_data(db: Session):
    """创建种子数据"""

    # ========== 1. 创建书柜 ==========
    bookshelf = Bookshelf(
        name="客厅书柜",
        location="客厅",
        width=100.0,
        height=200.0,
        description="主要藏书柜"
    )
    db.add(bookshelf)
    db.flush()  # 获取 ID
    print(f"✅ 创建书柜: {bookshelf.name} (ID: {bookshelf.id})")

    # ========== 2. 创建 3 个书架层 ==========
    shelves = []
    for level in range(1, 4):
        shelf = Shelf(
            bookshelf_id=bookshelf.id,
            level=level,
            height=30.0
        )
        db.add(shelf)
        shelves.append(shelf)
    db.flush()
    print(f"✅ 创建 {len(shelves)} 个书架层")

    # ========== 3. 创建分类 ==========
    categories = [
        Category(code="I", name="文学", level=1),
        Category(code="I2", name="中国文学", level=2, parent_id=None),
        Category(code="I247", name="小说", level=3, parent_id=None),
        Category(code="TP", name="自动化技术、计算机技术", level=1),
        Category(code="TP3", name="计算技术、计算机技术", level=2, parent_id=None),
        Category(code="TP311", name="程序设计、软件工程", level=3, parent_id=None),
    ]

    # 设置父子关系
    categories[1].parent_id = categories[0].id
    categories[2].parent_id = categories[1].id
    categories[4].parent_id = categories[3].id
    categories[5].parent_id = categories[4].id

    for cat in categories:
        db.add(cat)
    db.flush()
    print(f"✅ 创建 {len(categories)} 个分类")

    # ========== 4. 创建测试图书 ==========

    # 书籍 1: 三体
    work1 = Work(
        title="三体",
        subtitle="地球往事三部曲之一",
        description="刘慈欣创作的科幻小说",
        language="zh"
    )
    db.add(work1)
    db.flush()

    edition1 = Edition(
        work_id=work1.id,
        title="三体",
        isbn13="9787536692930",
        publisher="重庆出版社",
        publish_date="2008-01",
        page_count=302,
        source="manual"
    )
    db.add(edition1)
    db.flush()

    book1 = Book(
        edition_id=edition1.id,
        status="available",
        owner="测试用户",
        notes="好书",
        confidence=0.95
    )
    db.add(book1)
    db.flush()

    # 放置到书架第 1 层
    pos1 = ShelfPosition(
        book_id=book1.id,
        shelf_id=shelves[0].id,
        position_x=0.1,
        position_order=1
    )
    db.add(pos1)
    print(f"✅ 创建图书: {work1.title}")

    # 书籍 2: Python 编程
    work2 = Work(
        title="Python编程：从入门到实践",
        description="Python 入门经典教材",
        language="zh"
    )
    db.add(work2)
    db.flush()

    edition2 = Edition(
        work_id=work2.id,
        title="Python编程：从入门到实践",
        isbn13="9787115428028",
        publisher="人民邮电出版社",
        publish_date="2016-07",
        page_count=459,
        source="manual"
    )
    db.add(edition2)
    db.flush()

    book2 = Book(
        edition_id=edition2.id,
        status="available",
        owner="测试用户",
        confidence=0.90
    )
    db.add(book2)
    db.flush()

    # 放置到书架第 2 层
    pos2 = ShelfPosition(
        book_id=book2.id,
        shelf_id=shelves[1].id,
        position_x=0.2,
        position_order=1
    )
    db.add(pos2)
    print(f"✅ 创建图书: {work2.title}")

    # 书籍 3: 置身事内
    work3 = Work(
        title="置身事内",
        subtitle="中国政府与经济发展",
        description="兰小欢著，解读中国经济",
        language="zh"
    )
    db.add(work3)
    db.flush()

    edition3 = Edition(
        work_id=work3.id,
        title="置身事内",
        isbn13="9787208171336",
        publisher="上海人民出版社",
        publish_date="2021-08",
        page_count=320,
        source="manual"
    )
    db.add(edition3)
    db.flush()

    book3 = Book(
        edition_id=edition3.id,
        status="available",
        owner="测试用户",
        confidence=0.88
    )
    db.add(book3)
    db.flush()

    # 放置到书架第 1 层
    pos3 = ShelfPosition(
        book_id=book3.id,
        shelf_id=shelves[0].id,
        position_x=0.3,
        position_order=2
    )
    db.add(pos3)
    print(f"✅ 创建图书: {work3.title}")

    # 提交事务
    db.commit()
    print("\n🎉 Seed data 创建完成!")


def verify_data(db: Session):
    """验证数据"""
    print("\n📊 数据验证:")

    # 验证 Work
    works = db.query(Work).all()
    print(f"   Work 数量: {len(works)}")

    # 验证 Edition
    editions = db.query(Edition).all()
    print(f"   Edition 数量: {len(editions)}")

    # 验证 Book
    books = db.query(Book).all()
    print(f"   Book 数量: {len(books)}")

    # 验证 Bookshelf
    bookshelves = db.query(Bookshelf).all()
    print(f"   Bookshelf 数量: {len(bookshelves)}")

    # 验证 Shelf
    shelves = db.query(Shelf).all()
    print(f"   Shelf 数量: {len(shelves)}")

    # 验证 ShelfPosition
    positions = db.query(ShelfPosition).all()
    print(f"   ShelfPosition 数量: {len(positions)}")

    # 验证 Category
    categories = db.query(Category).all()
    print(f"   Category 数量: {len(categories)}")

    # 验证 Book-ShelfPosition 关系
    print("\n📚 书籍位置信息:")
    for book in books:
        edition = db.query(Edition).filter(Edition.id == book.edition_id).first()
        positions = db.query(ShelfPosition).filter(ShelfPosition.book_id == book.id).all()
        for pos in positions:
            shelf = db.query(Shelf).filter(Shelf.id == pos.shelf_id).first()
            bookshelf = db.query(Bookshelf).filter(Bookshelf.id == shelf.bookshelf_id).first()
            print(f"   《{edition.title}》-> {bookshelf.name} 第{shelf.level}层")


if __name__ == "__main__":
    from sqlalchemy.orm import sessionmaker
    SessionLocal = sessionmaker(bind=sync_engine)
    db = SessionLocal()

    try:
        create_seed_data(db)
        verify_data(db)
    except Exception as e:
        print(f"❌ 错误: {e}")
        db.rollback()
        raise
    finally:
        db.close()
