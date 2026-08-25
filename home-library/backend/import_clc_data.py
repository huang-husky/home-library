"""
中图法数据导入脚本
Phase 9: Classification System

使用方法:
    python import_clc_data.py

说明:
    - 本脚本导入的是简化的中图法数据
    - 完整数据需要从国家图书馆出版社等官方渠道获取
    - 本数据仅供学习和研究使用
"""
import asyncio
import sys
from pathlib import Path

# 添加 backend 到路径
sys.path.insert(0, str(Path(__file__).parent))

from sqlalchemy import select
from app.db.database import async_engine, AsyncSessionLocal
from app.models.models import Category
from app.data.clc_data import get_all_categories


async def import_clc_data():
    """导入中图法数据"""
    print("开始导入中图法分类数据...")

    async with AsyncSessionLocal() as db:
        # 检查是否已有数据
        result = await db.execute(select(Category))
        existing = result.scalars().all()

        if existing:
            print(f"数据库中已有 {len(existing)} 个分类")
            response = input("是否清空并重新导入? (y/n): ")
            if response.lower() == 'y':
                for cat in existing:
                    await db.delete(cat)
                await db.commit()
                print("已清空现有数据")
            else:
                print("取消导入")
                return

        # 获取所有分类数据
        categories = get_all_categories()
        print(f"准备导入 {len(categories)} 个分类...")

        # 创建 code 到 id 的映射（用于设置 parent_id）
        code_to_id = {}

        # 先导入一级分类
        for cat_data in categories:
            if cat_data["level"] == 1:
                category = Category(
                    code=cat_data["code"],
                    name=cat_data["name"],
                    description=cat_data.get("description", ""),
                    parent_id=None,
                    level=1,
                )
                db.add(category)
                await db.flush()
                code_to_id[cat_data["code"]] = category.id
                print(f"  导入一级分类: {cat_data['code']} - {cat_data['name']}")

        # 导入二级分类
        for cat_data in categories:
            if cat_data["level"] == 2:
                parent_code = cat_data["parent"]
                parent_id = code_to_id.get(parent_code)

                if not parent_id:
                    print(f"  警告: 未找到父分类 {parent_code}，跳过 {cat_data['code']}")
                    continue

                category = Category(
                    code=cat_data["code"],
                    name=cat_data["name"],
                    description=cat_data.get("description", ""),
                    parent_id=parent_id,
                    level=2,
                )
                db.add(category)
                await db.flush()
                code_to_id[cat_data["code"]] = category.id
                print(f"  导入二级分类: {cat_data['code']} - {cat_data['name']}")

        # 导入三级分类
        for cat_data in categories:
            if cat_data["level"] == 3:
                parent_code = cat_data["parent"]
                parent_id = code_to_id.get(parent_code)

                if not parent_id:
                    # 尝试使用前缀匹配
                    for code, id in code_to_id.items():
                        if parent_code.startswith(code):
                            parent_id = id
                            break

                if not parent_id:
                    print(f"  警告: 未找到父分类 {parent_code}，跳过 {cat_data['code']}")
                    continue

                category = Category(
                    code=cat_data["code"],
                    name=cat_data["name"],
                    description=cat_data.get("description", ""),
                    parent_id=parent_id,
                    level=3,
                )
                db.add(category)
                await db.flush()
                code_to_id[cat_data["code"]] = category.id

        await db.commit()

        # 统计
        result = await db.execute(select(Category))
        total = len(result.scalars().all())

        print(f"\n导入完成！")
        print(f"  总计: {total} 个分类")
        print(f"  一级分类: {len([c for c in categories if c['level'] == 1])}")
        print(f"  二级分类: {len([c for c in categories if c['level'] == 2])}")
        print(f"  三级分类: {len([c for c in categories if c['level'] == 3])}")


async def show_statistics():
    """显示分类统计"""
    async with AsyncSessionLocal() as db:
        result = await db.execute(select(Category))
        categories = result.scalars().all()

        if not categories:
            print("数据库中没有分类数据")
            return

        level1 = [c for c in categories if c.level == 1]
        level2 = [c for c in categories if c.level == 2]
        level3 = [c for c in categories if c.level == 3]

        print(f"\n分类统计:")
        print(f"  总计: {len(categories)} 个分类")
        print(f"  一级分类: {len(level1)}")
        print(f"  二级分类: {len(level2)}")
        print(f"  三级分类: {len(level3)}")

        print(f"\n一级分类列表:")
        for cat in sorted(level1, key=lambda x: x.code):
            children = [c for c in level2 if c.parent_id == cat.id]
            print(f"  {cat.code} - {cat.name} ({len(children)} 个子分类)")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="中图法数据导入工具")
    parser.add_argument("action", choices=["import", "stats", "clear"], help="操作")

    args = parser.parse_args()

    if args.action == "import":
        asyncio.run(import_clc_data())
    elif args.action == "stats":
        asyncio.run(show_statistics())
    elif args.action == "clear":
        confirm = input("确定要清空所有分类数据吗? 这将删除所有分类关联! (y/n): ")
        if confirm.lower() == 'y':
            async def clear():
                async with AsyncSessionLocal() as db:
                    result = await db.execute(select(Category))
                    for cat in result.scalars().all():
                        await db.delete(cat)
                    await db.commit()
                    print("已清空所有分类数据")
            asyncio.run(clear())
