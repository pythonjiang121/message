import pytest
import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from business import BusinessValidator

def test_link_deduction():
    validator = BusinessValidator()
    # 测试会销普通场景下的链接扣分
    result = validator._score_marketing(
        business_type="会销-普通",
        cleaned_content="请点击链接：http://example.com",
        cleaned_signature=""
    )
    assert result[0]  # 确保验证通过
    print("\nDeduction details:", validator.score_details['deductions'])
    # 检查扣分是否为-30
    assert any("链接扣分: -30" in detail for detail in validator.score_details['deductions'])

def test_fixed_phone_deduction():
    validator = BusinessValidator()
    # 测试固定电话扣分
    result = validator._score_marketing(
        business_type="会销-普通",
        cleaned_content="联系电话：021-12345678",
        cleaned_signature=""
    )
    assert result[0]  # 确保验证通过
    print("\nDeduction details:", validator.score_details['deductions'])
    # 检查扣分是否为-30 (更新为当前规则值)
    assert any("固定电话扣分: -30" in detail for detail in validator.score_details['deductions'])

def test_cooccurrence_enhancement():
    validator = BusinessValidator()
    # 测试链接和固定电话共现增强
    result = validator._score_marketing(
        business_type="会销-普通",
        cleaned_content="请点击链接：http://example.com 联系电话：021-12345678",
        cleaned_signature=""
    )
    assert result[0]  # 确保验证通过
    print("\nDeduction details:", validator.score_details['deductions'])
    # 检查链接扣分是否增强了50%
    link_deduction_detail = next((detail for detail in validator.score_details['deductions'] if "链接扣分" in detail), None)
    assert link_deduction_detail is not None
    assert "共现增强" in link_deduction_detail 