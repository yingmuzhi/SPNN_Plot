#!/usr/bin/env python3
"""
SVG分区上色渲染脚本
直接修改SVG文件，保持原始形状和曲线，只改变填充颜色
"""

import xml.etree.ElementTree as ET
import os
import argparse
from typing import Dict, List
import re

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="SVG分区上色渲染脚本")
    parser.add_argument(
        "--svg-file",
        default="/data/SegPNN_CR/_ymz/20250909_Figure02/coordinate/test.svg",
        help="SVG文件路径 (default: %(default)s)",
    )
    parser.add_argument(
        "--output-dir",
        default="/data/SegPNN_CR/_ymz/20250909_Figure02/output_spinal_render",
        help="输出目录 (default: %(default)s)",
    )
    return parser.parse_args()

# 手动指定的区域颜色映射
# 您可以在这里自定义每个区域的颜色
# 支持的颜色格式：十六进制（如 '#1f77b4'）、RGB（如 'rgb(31,119,180)'）、颜色名称（如 'blue'）
REGION_COLORS = {
    1: '#1f77b4',  # 区域1 - 蓝色
    2: '#ff7f0e',  # 区域2 - 橙色
    3: '#2ca02c',  # 区域3 - 绿色
    4: '#d62728',  # 区域4 - 红色
    5: '#9467bd',  # 区域5 - 紫色
    6: '#8c564b',  # 区域6 - 棕色
    7: '#e377c2',  # 区域7 - 粉色
    8: '#7f7f7f',  # 区域8 - 灰色
    9: '#bcbd22',  # 区域9 - 橄榄色
    10: '#17becf', # 区域10 - 青色
}

# 使用示例：
# 如果您想修改区域1的颜色为红色，区域2的颜色为绿色，可以这样修改：
# REGION_COLORS = {
#     1: 'red',     # 区域1 - 红色
#     2: 'green',   # 区域2 - 绿色
#     3: '#2ca02c', # 区域3 - 绿色（保持原色）
#     # ... 其他区域
# }

# 默认颜色（当区域数量超过预定义颜色时）
DEFAULT_COLORS = [
    '#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
    '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
    '#aec7e8', '#ffbb78', '#98df8a', '#ff9896', '#c5b0d5',
    '#c49c94', '#f7b6d3', '#c7c7c7', '#dbdb8d', '#9edae5'
]

class SVGColorRenderer:
    """SVG颜色渲染器 - 直接修改SVG文件保持原始形状"""
    
    def __init__(self, svg_file: str):
        self.svg_file = svg_file
        self.tree = ET.parse(svg_file)
        self.root = self.tree.getroot()
        
        # 获取SVG的viewBox
        viewbox = self.root.get('viewBox', '0 0 100 100')
        self.viewbox = [float(x) for x in viewbox.split()]
        self.width = self.viewbox[2]
        self.height = self.viewbox[3]
        
        print(f"SVG尺寸: {self.width} x {self.height}")
    
    def extract_paths_and_polygons(self) -> List[Dict]:
        """提取SVG中的所有路径和多边形"""
        elements = []
        
        # 查找所有path元素
        for i, path_elem in enumerate(self.root.findall('.//{http://www.w3.org/2000/svg}path')):
            elements.append({
                'element': path_elem,
                'type': 'path',
                'index': i + 1,
                'class': path_elem.get('class', ''),
                'id': path_elem.get('id', ''),
                'd': path_elem.get('d', '')
            })
        
        # 查找所有polygon元素
        for i, poly_elem in enumerate(self.root.findall('.//{http://www.w3.org/2000/svg}polygon')):
            elements.append({
                'element': poly_elem,
                'type': 'polygon',
                'index': i + 1,
                'class': poly_elem.get('class', ''),
                'id': poly_elem.get('id', ''),
                'points': poly_elem.get('points', '')
            })
        
        print(f"找到 {len(elements)} 个图形元素")
        return elements
    
    def apply_colors_to_svg(self, elements: List[Dict], region_colors: Dict[int, str], 
                           output_file: str) -> str:
        """直接修改SVG文件，应用颜色"""
        
        # 创建新的SVG根元素，保持所有原始属性
        new_root = ET.Element(self.root.tag, self.root.attrib)
        
        # 复制所有命名空间声明
        for key, value in self.root.attrib.items():
            if key.startswith('{'):
                new_root.set(key, value)
        
        # 复制所有子元素，但跳过要修改的path和polygon，以及style元素
        elements_to_modify = {elem['element'] for elem in elements}
        
        for child in self.root:
            if child not in elements_to_modify and child.tag != '{http://www.w3.org/2000/svg}style':
                # 直接复制非path/polygon/style元素
                new_root.append(child)
        
        # 为每个图形元素应用颜色
        region_idx = 1
        for elem_data in elements:
            element = elem_data['element']
            elem_type = elem_data['type']
            
            # 选择颜色
            if region_idx in region_colors:
                color = region_colors[region_idx]
            else:
                color = DEFAULT_COLORS[(region_idx - 1) % len(DEFAULT_COLORS)]
            
            # 创建新的元素，保持所有原始属性
            if elem_type == 'path':
                new_elem = ET.Element('path', element.attrib)
                # 只修改fill属性，保持其他所有属性不变
                new_elem.set('fill', color)
                # 确保有stroke属性
                if 'stroke' not in new_elem.attrib:
                    new_elem.set('stroke', '#000000')
                if 'stroke-width' not in new_elem.attrib:
                    new_elem.set('stroke-width', '1')
                if 'stroke-miterlimit' not in new_elem.attrib:
                    new_elem.set('stroke-miterlimit', '10')
            else:  # polygon
                new_elem = ET.Element('polygon', element.attrib)
                # 只修改fill属性，保持其他所有属性不变
                new_elem.set('fill', color)
                # 确保有stroke属性
                if 'stroke' not in new_elem.attrib:
                    new_elem.set('stroke', '#000000')
                if 'stroke-width' not in new_elem.attrib:
                    new_elem.set('stroke-width', '1')
                if 'stroke-miterlimit' not in new_elem.attrib:
                    new_elem.set('stroke-miterlimit', '10')
            
            new_root.append(new_elem)
            region_idx += 1
        
        # 创建新的树
        new_tree = ET.ElementTree(new_root)
        
        # 保存SVG文件
        new_tree.write(output_file, encoding='utf-8', xml_declaration=True)
        
        print(f"已保存彩色SVG: {output_file}")
        return output_file
    
    def create_region_info(self, elements: List[Dict], region_colors: Dict[int, str], 
                          output_file: str):
        """创建区域信息文件"""
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write("区域信息:\n")
            f.write("=" * 50 + "\n")
            
            region_idx = 1
            for elem_data in elements:
                elem_type = elem_data['type']
                class_name = elem_data['class']
                element_id = elem_data['id']
                
                # 选择颜色
                if region_idx in region_colors:
                    color = region_colors[region_idx]
                else:
                    color = DEFAULT_COLORS[(region_idx - 1) % len(DEFAULT_COLORS)]
                
                # 创建区域名称
                if element_id:
                    region_name = f"区域{region_idx}_{element_id}"
                elif class_name:
                    region_name = f"区域{region_idx}_{class_name}"
                else:
                    region_name = f"区域{region_idx}"
                
                f.write(f"区域 {region_idx}: {region_name}\n")
                f.write(f"  类型: {elem_type}\n")
                f.write(f"  颜色: {color}\n")
                f.write(f"  Class: {class_name}\n")
                f.write(f"  ID: {element_id}\n")
                f.write("-" * 30 + "\n")
                
                region_idx += 1

def main():
    """主函数"""
    args = parse_args()
    
    svg_file = args.svg_file
    output_dir = args.output_dir
    
    # 确保输出目录存在
    os.makedirs(output_dir, exist_ok=True)
    
    if not os.path.exists(svg_file):
        print(f"SVG文件不存在: {svg_file}")
        return
    
    print("开始处理SVG文件...")
    
    # 创建SVG颜色渲染器
    renderer = SVGColorRenderer(svg_file)
    
    # 提取图形元素
    elements = renderer.extract_paths_and_polygons()
    
    if not elements:
        print("未找到任何图形元素")
        return
    
    # 应用颜色并保存SVG
    output_svg = os.path.join(output_dir, "colored_regions.svg")
    renderer.apply_colors_to_svg(elements, REGION_COLORS, output_svg)
    
    # 创建区域信息文件
    region_info_file = os.path.join(output_dir, "region_info.txt")
    renderer.create_region_info(elements, REGION_COLORS, region_info_file)
    
    print(f"区域信息已保存到: {region_info_file}")
    print(f"渲染完成！输出文件: {output_svg}")
    print("\n特点:")
    print("- 完全保持原始SVG的形状和曲线")
    print("- 只改变填充颜色，保持所有其他属性")
    print("- 保持原始的stroke、stroke-width等属性")

if __name__ == "__main__":
    main()