"""Export service for analytics data (CSV and PDF)."""
import csv
import io
from datetime import datetime, date
from typing import List, Dict, Any
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.platypus import Image as RLImage
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import logging

logger = logging.getLogger(__name__)


class ExportService:
    """Service for exporting analytics data"""
    
    @staticmethod
    def export_to_csv(data: List[Dict[str, Any]], filename: str = "export.csv") -> io.BytesIO:
        """
        Export data to CSV format.
        
        Args:
            data: List of dictionaries containing data
            filename: Output filename
            
        Returns:
            BytesIO: CSV file content
        """
        output = io.BytesIO()
        
        if not data:
            return output
        
        # Get headers from first row
        headers = list(data[0].keys())
        
        # Create CSV writer
        output_text = io.StringIO()
        writer = csv.DictWriter(output_text, fieldnames=headers)
        
        # Write headers and data
        writer.writeheader()
        writer.writerows(data)
        
        # Convert to bytes
        output.write(output_text.getvalue().encode('utf-8'))
        output.seek(0)
        
        return output
    
    @staticmethod
    def export_statistics_to_csv(stats_data: Dict[str, Any]) -> io.BytesIO:
        """Export comprehensive statistics to CSV."""
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Overall statistics
        writer.writerow(['OVERALL STATISTICS'])
        writer.writerow(['Metric', 'Value'])
        writer.writerow(['Total Downloads', stats_data.get('total_downloads', 0)])
        writer.writerow(['Total Page Views', stats_data.get('total_page_views', 0)])
        writer.writerow(['Today Downloads', stats_data.get('today_downloads', 0)])
        writer.writerow(['Today Views', stats_data.get('today_views', 0)])
        writer.writerow(['This Month Downloads', stats_data.get('this_month_downloads', 0)])
        writer.writerow(['This Month Views', stats_data.get('this_month_views', 0)])
        writer.writerow([])
        
        # Daily statistics
        if 'daily_stats' in stats_data:
            writer.writerow(['DAILY STATISTICS'])
            writer.writerow(['Date', 'Downloads', 'Page Views'])
            for stat in stats_data['daily_stats']:
                writer.writerow([stat['date'], stat['downloads'], stat['page_views']])
            writer.writerow([])
        
        # Monthly statistics
        if 'monthly_stats' in stats_data:
            writer.writerow(['MONTHLY STATISTICS'])
            writer.writerow(['Month', 'Downloads', 'Page Views'])
            for stat in stats_data['monthly_stats']:
                writer.writerow([stat['month'], stat['downloads'], stat['page_views']])
        
        # Convert to bytes
        bytes_output = io.BytesIO()
        bytes_output.write(output.getvalue().encode('utf-8'))
        bytes_output.seek(0)
        
        return bytes_output
    
    @staticmethod
    def export_to_pdf(
        title: str,
        data: List[Dict[str, Any]],
        stats: Dict[str, Any] = None,
        filename: str = "export.pdf"
    ) -> io.BytesIO:
        """
        Export data to PDF format with professional styling.
        
        Args:
            title: Report title
            data: List of dictionaries containing data
            stats: Optional overall statistics
            filename: Output filename
            
        Returns:
            BytesIO: PDF file content
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        
        # Container for PDF elements
        elements = []
        
        # Styles
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=16,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        # Title
        title_para = Paragraph(title, title_style)
        elements.append(title_para)
        elements.append(Spacer(1, 0.3*inch))
        
        # Generated date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        date_para = Paragraph(f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", date_style)
        elements.append(date_para)
        elements.append(Spacer(1, 0.5*inch))
        
        # Overall Statistics (if provided)
        if stats:
            elements.append(Paragraph("Overall Statistics", heading_style))
            
            stats_data = [
                ['Metric', 'Value'],
                ['Total Downloads', f"{stats.get('total_downloads', 0):,}"],
                ['Total Page Views', f"{stats.get('total_page_views', 0):,}"],
                ['Today Downloads', f"{stats.get('today_downloads', 0):,}"],
                ['Today Views', f"{stats.get('today_views', 0):,}"],
                ['This Month Downloads', f"{stats.get('this_month_downloads', 0):,}"],
                ['This Month Views', f"{stats.get('this_month_views', 0):,}"],
            ]
            
            stats_table = Table(stats_data, colWidths=[3*inch, 2*inch])
            stats_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 10),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            elements.append(stats_table)
            elements.append(Spacer(1, 0.5*inch))
        
        # Detailed Data Table
        if data and len(data) > 0:
            elements.append(Paragraph("Detailed Statistics", heading_style))
            
            # Get headers
            headers = list(data[0].keys())
            table_data = [headers]
            
            # Add data rows
            for row in data:
                table_data.append([str(row.get(h, '')) for h in headers])
            
            # Calculate column widths
            col_width = 6.5*inch / len(headers)
            col_widths = [col_width] * len(headers)
            
            # Create table
            data_table = Table(table_data, colWidths=col_widths)
            data_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('GRID', (0, 0), (-1, -1), 1, colors.black),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 9),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
            ]))
            
            elements.append(data_table)
        
        # Footer
        elements.append(Spacer(1, 0.5*inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=8,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        footer_para = Paragraph(
            "© 2025 Video Downloader Admin Panel - Confidential Report",
            footer_style
        )
        elements.append(footer_para)
        
        # Build PDF
        doc.build(elements)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def export_analytics_pdf(
        overall_stats: Dict[str, Any],
        daily_stats: List[Dict[str, Any]],
        monthly_stats: List[Dict[str, Any]]
    ) -> io.BytesIO:
        """Export comprehensive analytics report to PDF."""
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=28,
            textColor=colors.HexColor('#667eea'),
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        # Title
        elements.append(Paragraph("📊 Analytics Report", title_style))
        elements.append(Spacer(1, 0.5*inch))
        
        # Date
        date_style = ParagraphStyle(
            'DateStyle',
            parent=styles['Normal'],
            fontSize=12,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            f"Report Date: {datetime.now().strftime('%B %d, %Y')}",
            date_style
        ))
        elements.append(Spacer(1, 0.5*inch))
        
        # Overall Statistics
        heading_style = ParagraphStyle(
            'Heading',
            parent=styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#333333'),
            spaceAfter=12,
            spaceBefore=12
        )
        
        elements.append(Paragraph("📈 Overall Performance", heading_style))
        
        overall_data = [
            ['Metric', 'Value', 'Description'],
            ['Total Downloads', f"{overall_stats['total_downloads']:,}", 'All-time downloads'],
            ['Total Page Views', f"{overall_stats['total_page_views']:,}", 'All-time page views'],
            ['Today Downloads', f"{overall_stats['today_downloads']:,}", 'Downloads today'],
            ['Today Views', f"{overall_stats['today_views']:,}", 'Page views today'],
            ['Monthly Downloads', f"{overall_stats['this_month_downloads']:,}", 'Downloads this month'],
            ['Monthly Views', f"{overall_stats['this_month_views']:,}", 'Views this month'],
        ]
        
        overall_table = Table(overall_data, colWidths=[2*inch, 1.5*inch, 2.5*inch])
        overall_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#667eea')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (1, -1), 'LEFT'),
            ('ALIGN', (1, 1), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(overall_table)
        elements.append(PageBreak())
        
        # Daily Statistics
        elements.append(Paragraph("📅 Daily Statistics (Last 30 Days)", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        daily_data = [['Date', 'Downloads', 'Page Views', 'Total Activity']]
        for stat in daily_stats[:30]:  # Limit to 30 days
            total = stat['downloads'] + stat['page_views']
            daily_data.append([
                stat['date'],
                str(stat['downloads']),
                str(stat['page_views']),
                str(total)
            ])
        
        daily_table = Table(daily_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        daily_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#764ba2')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(daily_table)
        elements.append(PageBreak())
        
        # Monthly Statistics
        elements.append(Paragraph("📊 Monthly Statistics", heading_style))
        elements.append(Spacer(1, 0.2*inch))
        
        monthly_data = [['Month', 'Downloads', 'Page Views', 'Total Activity']]
        for stat in monthly_stats:
            total = stat['downloads'] + stat['page_views']
            monthly_data.append([
                stat['month'],
                f"{stat['downloads']:,}",
                f"{stat['page_views']:,}",
                f"{total:,}"
            ])
        
        monthly_table = Table(monthly_data, colWidths=[2*inch, 1.5*inch, 1.5*inch, 1.5*inch])
        monthly_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#4caf50')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey]),
        ]))
        
        elements.append(monthly_table)
        
        # Footer
        elements.append(Spacer(1, inch))
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.grey,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(
            "Generated by Video Downloader Admin Panel<br/>"
            "© 2025 All Rights Reserved - Confidential Document",
            footer_style
        ))
        
        doc.build(elements)
        buffer.seek(0)
        
        return buffer

