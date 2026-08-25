"""
书架识别 API 测试脚本
Phase 7: Shelf Image Recognition MVP

用法:
    python test_scan_api.py

或 curl:
    # 1. 上传图片识别
    curl -X POST "http://localhost:8000/scans/upload" \
         -F "file=@your_bookshelf_photo.jpg" \
         -F "bookshelf_id=1" \
         -F "shelf_id=1"

    # 2. 获取扫描列表
    curl "http://localhost:8000/scans"

    # 3. 获取扫描详情
    curl "http://localhost:8000/scans/1"

    # 4. 更新识别项（编辑文本）
    curl -X PATCH "http://localhost:8000/scans/items/1" \
         -H "Content-Type: application/json" \
         -d '{"detected_text": "三体"}'

    # 5. 确认/拒绝识别项
    curl -X PATCH "http://localhost:8000/scans/items/1" \
         -H "Content-Type: application/json" \
         -d '{"status": "confirmed"}'

    # 6. 删除误检
    curl -X DELETE "http://localhost:8000/scans/items/1"

    # 7. 手动添加漏检
    curl -X POST "http://localhost:8000/scans/1/items" \
         -F "text=书名" \
         -F "bbox_x=0.1" \
         -F "bbox_y=0.2" \
         -F "bbox_width=0.15" \
         -F "bbox_height=0.8"

    # 8. 获取统计
    curl "http://localhost:8000/scans/1/stats"
"""
import requests
import sys
from pathlib import Path

BASE_URL = "http://localhost:8000"


def test_upload(image_path: str, bookshelf_id: int = None, shelf_id: int = None):
    """测试上传识别"""
    url = f"{BASE_URL}/scans/upload"

    files = {'file': open(image_path, 'rb')}
    data = {}
    if bookshelf_id:
        data['bookshelf_id'] = bookshelf_id
    if shelf_id:
        data['shelf_id'] = shelf_id

    print(f"📤 上传图片: {image_path}")
    response = requests.post(url, files=files, data=data)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 识别成功!")
        print(f"   扫描 ID: {result['scan_id']}")
        print(f"   检测到: {result['detected_count']} 本书")
        print(f"\n   识别结果:")
        for item in result['items']:
            conf_emoji = "🟢" if item['confidence'] >= 0.8 else "🟡" if item['confidence'] >= 0.5 else "🔴"
            print(f"   {conf_emoji} [{item['id']}] {item['detected_text']} ({item['confidence']:.1%})")
        return result['scan_id']
    else:
        print(f"❌ 错误: {response.status_code}")
        print(response.text)
        return None


def test_get_scan(scan_id: int):
    """测试获取扫描详情"""
    url = f"{BASE_URL}/scans/{scan_id}"
    response = requests.get(url)

    if response.status_code == 200:
        result = response.json()
        print(f"\n📋 扫描详情 (ID: {scan_id}):")
        print(f"   书柜: {result.get('bookshelf_id', 'N/A')}")
        print(f"   层: {result.get('shelf_id', 'N/A')}")
        print(f"   图片: {result['image_path']}")
        print(f"   识别项: {len(result['items'])}")
        return result
    else:
        print(f"❌ 获取失败: {response.status_code}")
        return None


def test_update_item(item_id: int, text: str = None, status: str = None):
    """测试更新识别项"""
    url = f"{BASE_URL}/scans/items/{item_id}"
    data = {}
    if text:
        data['detected_text'] = text
    if status:
        data['status'] = status

    response = requests.patch(url, json=data)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 更新成功: [{result['id']}] {result['detected_text']} (状态: {result['status']})")
        return result
    else:
        print(f"❌ 更新失败: {response.status_code}")
        return None


def test_get_stats(scan_id: int):
    """测试获取统计"""
    url = f"{BASE_URL}/scans/{scan_id}/stats"
    response = requests.get(url)

    if response.status_code == 200:
        stats = response.json()
        print(f"\n📊 统计信息:")
        print(f"   总数: {stats['total_items']}")
        print(f"   🟢 高置信度 (≥80%): {stats['high_confidence']}")
        print(f"   🟡 中置信度 (50-80%): {stats['medium_confidence']}")
        print(f"   🔴 低置信度 (<50%): {stats['low_confidence']}")
        print(f"   待确认: {stats['pending_count']}")
        print(f"   已确认: {stats['confirmed_count']}")
        print(f"   已拒绝: {stats['rejected_count']}")
        return stats
    else:
        print(f"❌ 获取统计失败: {response.status_code}")
        return None


def main():
    """主测试流程"""
    print("=" * 50)
    print("HomeLib Phase 7: 书架扫描 API 测试")
    print("=" * 50)

    # 检查服务是否运行
    try:
        health = requests.get(f"{BASE_URL}/health", timeout=3)
        print(f"✅ 服务状态: {health.json()}")
    except:
        print(f"❌ 无法连接到 {BASE_URL}")
        print("   请先启动后端服务: uvicorn app.main:app --reload")
        sys.exit(1)

    # 创建测试图片（如果没有提供）
    from PIL import Image
    test_image = Path("test_bookshelf.jpg")

    if not test_image.exists():
        print("\n📸 创建测试图片...")
        # 创建一个模拟的书架图片
        img = Image.new('RGB', (1200, 800), color='#8B4513')  # 棕色背景

        # 添加一些白色矩形模拟书脊
        from PIL import ImageDraw
        draw = ImageDraw.Draw(img)

        colors = ['#FF6B6B', '#4ECDC4', '#45B7D1', '#96CEB4', '#FFEAA7', '#DDA0DD', '#98D8C8']
        x = 50
        for i, color in enumerate(colors * 5):  # 25本书
            width = 30 + (i % 3) * 10
            if x + width > 1150:
                break
            draw.rectangle([x, 100, x + width, 700], fill=color, outline='#333', width=2)
            x += width + 5

        img.save(test_image)
        print(f"   已创建: {test_image}")

    # 测试 1: 上传识别
    scan_id = test_upload(str(test_image), bookshelf_id=1, shelf_id=1)

    if not scan_id:
        print("\n❌ 测试失败，退出")
        sys.exit(1)

    # 测试 2: 获取详情
    test_get_scan(scan_id)

    # 测试 3: 获取统计
    test_get_stats(scan_id)

    print("\n" + "=" * 50)
    print("测试完成!")
    print(f"可以在浏览器打开: http://localhost:5173/scan")
    print("=" * 50)


if __name__ == "__main__":
    main()
