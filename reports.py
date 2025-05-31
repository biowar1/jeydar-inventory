import streamlit as st
from firebase_config import get_db
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

def app():
    st.title("📊 Inventory Reports & Analytics")
    
    db = get_db()
    if not db:
        st.error("Database connection failed")
        return
    
    try:
        # Get all inventory items
        items = []
        docs = db.collection('inventory').stream()
        
        for doc in docs:
            item = doc.to_dict()
            item['id'] = doc.id
            items.append(item)
        
        if not items:
            st.info("No inventory data available for reports.")
            return
        
        df = pd.DataFrame(items)
        
        # Summary metrics
        st.subheader("📈 Summary Metrics")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_items = len(df)
            st.metric("Total Items", total_items)
        
        with col2:
            total_quantity = df['quantity'].sum()
            st.metric("Total Quantity", total_quantity)
        
        with col3:
            total_value = (df['quantity'] * df['price']).sum()
            st.metric("Total Value", f"${total_value:,.2f}")
        
        with col4:
            low_stock_items = len(df[df['quantity'] < 10])  # Assuming 10 is low stock threshold
            st.metric("Low Stock Items", low_stock_items)
        
        st.markdown("---")
        
        # Charts
        tab1, tab2, tab3 = st.tabs(["Category Analysis", "Stock Levels", "Value Analysis"])
        
        with tab1:
            st.subheader("Items by Category")
            
            # Category distribution
            category_counts = df['category'].value_counts()
            fig_pie = px.pie(values=category_counts.values, names=category_counts.index, 
                           title="Distribution of Items by Category")
            st.plotly_chart(fig_pie, use_container_width=True)
            
            # Category quantity
            category_qty = df.groupby('category')['quantity'].sum().reset_index()
            fig_bar = px.bar(category_qty, x='category', y='quantity', 
                           title="Total Quantity by Category")
            st.plotly_chart(fig_bar, use_container_width=True)
        
        with tab2:
            st.subheader("Stock Level Analysis")
            
            # Stock levels
            fig_stock = px.bar(df, x='name', y='quantity', color='category',
                             title="Stock Levels by Item")
            fig_stock.update_xaxis(tickangle=45)
            st.plotly_chart(fig_stock, use_container_width=True)
            
            # Low stock alert
            st.subheader("🚨 Low Stock Alert")
            low_stock_threshold = st.slider("Set Low Stock Threshold", 1, 50, 10)
            low_stock_df = df[df['quantity'] < low_stock_threshold]
            
            if not low_stock_df.empty:
                st.warning(f"Found {len(low_stock_df)} items with low stock!")
                st.dataframe(low_stock_df[['name', 'category', 'quantity', 'price']], use_container_width=True)
            else:
                st.success("All items are well stocked!")
        
        with tab3:
            st.subheader("Value Analysis")
            
            # Calculate total value per item
            df['total_value'] = df['quantity'] * df['price']
            
            # Top valuable items
            top_valuable = df.nlargest(10, 'total_value')
            fig_value = px.bar(top_valuable, x='name', y='total_value', 
                             title="Top 10 Most Valuable Items")
            fig_value.update_xaxis(tickangle=45)
            st.plotly_chart(fig_value, use_container_width=True)
            
            # Value by category
            category_value = df.groupby('category')['total_value'].sum().reset_index()
            fig_cat_value = px.pie(category_value, values='total_value', names='category',
                                 title="Total Value by Category")
            st.plotly_chart(fig_cat_value, use_container_width=True)
        
        st.markdown("---")
        
        # Export functionality
        st.subheader("📥 Export Data")
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📊 Download Inventory Report (CSV)"):
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"inventory_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
        
        with col2:
            if st.button("📋 Generate Summary Report"):
                st.text_area("Summary Report", 
                           f"""
INVENTORY SUMMARY REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

Total Items: {total_items}
Total Quantity: {total_quantity}
Total Value: ${total_value:,.2f}
Low Stock Items: {low_stock_items}

Categories:
{category_counts.to_string()}
                           """, height=200)
        
    except Exception as e:
        st.error(f"Error generating reports: {e}")
