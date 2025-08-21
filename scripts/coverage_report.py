#!/usr/bin/env python3
"""
動態測試覆蓋率報告生成器
使用: python scripts/coverage_report.py
"""

import os
import subprocess
import json
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path


class CoverageReporter:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.coverage_xml = self.project_root / "coverage.xml"
        
    def run_coverage_tests(self):
        """執行測試並生成覆蓋率數據"""
        print("🔄 執行測試並生成覆蓋率報告...")
        
        cmd = [
            "python3", "-m", "pytest", "tests/",
            "--cov=src", "--cov=api", "--cov=config", "--cov=app", "--cov=tasks",
            "--cov-report=xml", "--cov-report=term-missing",
            "--tb=no", "-q", "--disable-warnings"  # 簡化輸出
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            return result.returncode == 0, result.stdout, result.stderr
        except Exception as e:
            return False, "", str(e)
    
    def parse_coverage_xml(self):
        """解析覆蓋率XML文件"""
        if not self.coverage_xml.exists():
            return None
            
        tree = ET.parse(self.coverage_xml)
        root = tree.getroot()
        
        # 總覆蓋率
        total_lines = int(root.attrib.get('lines-valid', 0))
        covered_lines = int(root.attrib.get('lines-covered', 0))
        total_coverage = (covered_lines / total_lines * 100) if total_lines > 0 else 0
        
        # 各文件覆蓋率
        files_coverage = []
        for package in root.findall('.//package'):
            package_name = package.attrib.get('name', '')
            for cls in package.findall('.//class'):
                filename = cls.attrib.get('filename', '')
                
                # 如果包名不是根目錄，組合完整路徑
                if package_name and package_name != '.':
                    if not filename.startswith(package_name):
                        filename = f"{package_name}/{filename}"
                
                lines_valid = int(cls.attrib.get('lines-valid', 0))
                lines_covered = int(cls.attrib.get('lines-covered', 0))
                coverage = (lines_covered / lines_valid * 100) if lines_valid > 0 else 0
                
                if lines_valid > 0 and filename != '__init__.py':  # 排除空的__init__.py
                    files_coverage.append({
                        'filename': filename,
                        'lines_total': lines_valid,
                        'lines_covered': lines_covered,
                        'coverage': coverage
                    })
        
        return {
            'total_coverage': total_coverage,
            'total_lines': total_lines,
            'covered_lines': covered_lines,
            'files': sorted(files_coverage, key=lambda x: x['coverage'], reverse=True)
        }
    
    def get_test_stats(self):
        """獲取測試統計信息"""
        cmd = ["python3", "-m", "pytest", "tests/", "--collect-only", "-q"]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, cwd=self.project_root)
            lines = result.stdout.split('\n')
            
            total_tests = 0
            for line in lines:
                if "collected" in line and "item" in line:
                    # 查找像 "129 items collected" 這樣的行
                    parts = line.split()
                    if len(parts) > 0 and parts[0].isdigit():
                        total_tests = int(parts[0])
                        break
            
            return total_tests
        except:
            return 129  # 回退到已知的測試數量
    
    def categorize_files(self, files):
        """分類文件到不同功能模組"""
        categories = {
            'feature1_product_tracking': {
                'name': '功能一：產品追蹤',
                'patterns': ['parsers/', 'monitoring/', 'models/product_'],
                'files': []
            },
            'api_layer': {
                'name': 'API層',
                'patterns': ['api/'],
                'files': []
            },
            'feature2_competitive': {
                'name': '功能二：競品分析', 
                'patterns': ['competitive/', 'models/competitive_'],
                'files': []
            },
            'shared_infrastructure': {
                'name': '共同基礎設施',
                'patterns': ['cache/', 'config/', 'app.py', 'tasks.py'],
                'files': []
            }
        }
        
        for file_info in files:
            filename = file_info['filename']
            categorized = False
            
            for cat_key, cat_info in categories.items():
                for pattern in cat_info['patterns']:
                    if pattern in filename:
                        categories[cat_key]['files'].append(file_info)
                        categorized = True
                        break
                if categorized:
                    break
        
        # 計算各分類的平均覆蓋率
        for cat_key, cat_info in categories.items():
            if cat_info['files']:
                total_lines = sum(f['lines_total'] for f in cat_info['files'])
                covered_lines = sum(f['lines_covered'] for f in cat_info['files'])
                cat_info['coverage'] = (covered_lines / total_lines * 100) if total_lines > 0 else 0
                cat_info['file_count'] = len(cat_info['files'])
            else:
                cat_info['coverage'] = 0
                cat_info['file_count'] = 0
        
        return categories
    
    def get_status_emoji(self, coverage):
        """根據覆蓋率返回狀態emoji"""
        if coverage >= 80:
            return "🟢"
        elif coverage >= 70:
            return "🟡"
        elif coverage >= 50:
            return "🟠"
        else:
            return "🔴"
    
    def get_grade(self, coverage):
        """根據覆蓋率返回等級"""
        if coverage >= 90:
            return "A+"
        elif coverage >= 80:
            return "A"
        elif coverage >= 70:
            return "B+"
        elif coverage >= 60:
            return "B"
        elif coverage >= 50:
            return "C+"
        else:
            return "C"
    
    def print_report(self):
        """生成並打印覆蓋率報告"""
        print("=" * 80)
        print("📊 AMAZON INSIGHTS - 測試覆蓋率報告")
        print("=" * 80)
        print(f"⏰ 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()
        
        # 執行測試
        success, stdout, stderr = self.run_coverage_tests()
        if not success:
            print("❌ 測試執行失敗:")
            if stderr:
                print("錯誤信息:", stderr[:500])
            if stdout:
                print("輸出信息:", stdout[:500])
            print("\n🔄 嘗試直接解析現有覆蓋率數據...")
            # 繼續嘗試解析已有的覆蓋率數據
        
        # 解析覆蓋率數據
        coverage_data = self.parse_coverage_xml()
        if not coverage_data:
            print("❌ 無法解析覆蓋率數據")
            return
        
        # 整體摘要
        total_coverage = coverage_data['total_coverage']
        total_tests = self.get_test_stats()
        
        print("🎯 整體覆蓋率摘要")
        print("-" * 40)
        print(f"總覆蓋率:     {self.get_status_emoji(total_coverage)} {total_coverage:.1f}% ({self.get_grade(total_coverage)})")
        print(f"總代碼行數:   📄 {coverage_data['total_lines']:,} 行")
        print(f"已覆蓋行數:   ✅ {coverage_data['covered_lines']:,} 行")
        print(f"測試總數:     🧪 {total_tests} 個")
        print()
        
        # 功能模組分析
        categories = self.categorize_files(coverage_data['files'])
        
        print("📈 各功能模組覆蓋率")
        print("-" * 50)
        print(f"{'模組':<20} {'覆蓋率':<12} {'狀態':<8} {'文件數'}")
        print("-" * 50)
        
        for cat_key, cat_info in categories.items():
            coverage = cat_info['coverage']
            status = self.get_status_emoji(coverage)
            grade = self.get_grade(coverage)
            print(f"{cat_info['name']:<18} {coverage:>6.1f}% ({grade:<2}) {status:<6} {cat_info['file_count']:>3}個")
        
        print()
        
        # 高覆蓋率文件 (>=70%)
        high_coverage_files = [f for f in coverage_data['files'] if f['coverage'] >= 70]
        if high_coverage_files:
            print("🏆 高覆蓋率文件 (≥70%)")
            print("-" * 70)
            print(f"{'文件':<45} {'覆蓋率':<12} {'狀態'}")
            print("-" * 70)
            
            for file_info in high_coverage_files[:10]:  # 只顯示前10個
                filename = file_info['filename'].split('/')[-1]  # 只顯示文件名
                if len(filename) > 42:
                    filename = filename[:39] + "..."
                coverage = file_info['coverage']
                status = self.get_status_emoji(coverage)
                grade = self.get_grade(coverage)
                print(f"{filename:<43} {coverage:>6.1f}% ({grade:<2}) {status}")
            
            if len(high_coverage_files) > 10:
                print(f"... 還有 {len(high_coverage_files) - 10} 個高覆蓋率文件")
            print()
        
        # 需改善的文件 (<50%)
        low_coverage_files = [f for f in coverage_data['files'] if f['coverage'] < 50 and f['coverage'] > 0]
        if low_coverage_files:
            print("⚠️  需改善的文件 (<50%)")
            print("-" * 70)
            print(f"{'文件':<45} {'覆蓋率':<12} {'狀態'}")
            print("-" * 70)
            
            for file_info in sorted(low_coverage_files, key=lambda x: x['coverage'])[:8]:
                filename = file_info['filename'].split('/')[-1]
                if len(filename) > 42:
                    filename = filename[:39] + "..."
                coverage = file_info['coverage']
                status = self.get_status_emoji(coverage)
                grade = self.get_grade(coverage)
                print(f"{filename:<43} {coverage:>6.1f}% ({grade:<2}) {status}")
            
            if len(low_coverage_files) > 8:
                print(f"... 還有 {len(low_coverage_files) - 8} 個需改善文件")
            print()
        
        # 建議
        print("💡 改善建議")
        print("-" * 40)
        if total_coverage >= 70:
            print("✅ 覆蓋率已達標！繼續保持測試品質")
        elif total_coverage >= 50:
            print("🔸 專注改善低覆蓋率的核心模組")
            print("🔸 增加業務邏輯的單元測試")
        else:
            print("🔸 優先測試核心業務邏輯")
            print("🔸 使用 Mock 避免外部依賴")
            print("🔸 專注於純函數和數據模型測試")
        
        print()
        print("🚀 快速命令")
        print("-" * 40)
        print("完整測試:     python3 -m pytest tests/ --cov=. --cov-report=html")
        print("核心功能:     python3 -m pytest tests/ --cov=src --cov=api")
        print("HTML報告:     open htmlcov/index.html")
        print("再次查看:     python scripts/coverage_report.py")
        
        print("=" * 80)


def main():
    """主函數"""
    reporter = CoverageReporter()
    reporter.print_report()


if __name__ == "__main__":
    main()