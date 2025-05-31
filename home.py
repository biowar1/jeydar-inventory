import streamlit as st
from firebase_config import get_db
import pandas as pd
import plotly.express as px
from datetime import datetime

def app():
    st.title("📦 Inventory Management Dashboard")
    
    # Welcome message
    user = st.session_state.get('user', {})
    st.markdown(f"### Welcome back, {user.get('username', 'User')}! 👋")
    
    # Get database connection
    db = get_db()
    
    if not db:
        st.error("Database connection failed")
        return
    
    try:
        # Get inventory data
        inventory_docs = list(db.collection('inventory').stream())
        items = []
        
        for doc in inventory_docs:
            item = doc.to_dict()
            item['id'] = doc.id
            items.append(item)
        
        # Display metrics
        col1, col2, col3, col4 = st.columns(4)
        
        if items:
            df = pd.DataFrame(items)
            
            total_items = len(items)
            total_quantity = df['quantity'].sum()
            total_value = (df['quantity'] * df['price']).sum()
            low_stock_items = len(df[df['quantity'] < 10])  # Items with less than 10 units
            
            with col1:
                st.metric("📦 Total Items", total_items)
            
            with col2:
                st.metric("📊 Total Quantity", f"{total_quantity:,}")
            
            with col3:
                st.metric("💰 Total Value", f"${total_value:,.2f}")
            
            with col4:
                st.metric("⚠️ Low Stock Items", low_stock_items, delta=f"-{low_stock_items}" if low_stock_items > 0 else "0")
        else:
            with col1:
                st.metric("📦 Total Items", "0")
            with col2:
                st.metric("📊 Total Quantity", "0")
            with col3:
                st.metric("💰 Total Value", "$0.00")
            with col4:
                st.metric("⚠️ Low Stock Items", "0")
        
        st.markdown("---")
        
        # Quick actions
        st.subheader("⚡ Quick Actions")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("➕ Add New Item", use_container_width=True, type="primary"):
                # Note: In Streamlit, we can't directly switch pages like this
                # Instead, we'll use session state to control navigation
                st.session_state.page_redirect = "inventory"
                st.rerun()
        
        with col2:
            if st.button("📊 View Reports", use_container_width=True):
                st.session_state.page_redirect = "reports"
                st.rerun()
        
        with col3:
            if st.button("📋 Full Inventory", use_container_width=True):
                st.session_state.page_redirect = "inventory"
                st.rerun()
        
        with col4:
            if st.button("👤 Account Settings", use_container_width=True):
                st.session_state.page_redirect = "account"
                st.rerun()
        
        st.markdown("---")
        
        # Recent activity and charts
        if items:
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 Category Distribution")
                category_counts = df['category'].value_counts()
                fig_pie = px.pie(
                    values=category_counts.values, 
                    names=category_counts.index,
                    title="Items by Category"
                )
                fig_pie.update_layout(height=400)
                st.plotly_chart(fig_pie, use_container_width=True)
            
            with col2:
                st.subheader("💰 Top 5 Valuable Items")
                df['total_value'] = df['quantity'] * df['price']
                top_items = df.nlargest(5, 'total_value')
                
                if not top_items.empty:
                    fig_bar = px.bar(
                        top_items, 
                        x='name', 
                        y='total_value',
                        title="Most Valuable Items",
                        color='category'
                    )
                    fig_bar.update_layout(height=400)
                    fig_bar.update_xaxis(tickangle=45)
                    st.plotly_chart(fig_bar, use_container_width=True)
                else:
                    st.info("No items to display")
            
            # Low stock alerts
            st.markdown("---")
            st.subheader("🚨 Alerts & Notifications")
            
            if low_stock_items > 0:
                st.warning(f"⚠️ {low_stock_items} items are running low on stock!")
                
                low_stock_df = df[df['quantity'] < 10]
                with st.expander("View Low Stock Items"):
                    st.dataframe(
                        low_stock_df[['name', 'category', 'quantity', 'price']].sort_values('quantity'),
                        use_container_width=True
                    )
            else:
                st.success("✅ All items are well stocked!")
            
            # Recent items (last 5 added)
            st.markdown("---")
            st.subheader("🕒 Recently Added Items")
            
            # Sort by creation time if available, otherwise show last 5
            recent_items = df.tail(5) if len(df) > 5 else df
            
            if not recent_items.empty:
                for _, item in recent_items.iterrows():
                    with st.container():
                        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])
                        
                        with col1:
                            st.write(f"**{item['name']}**")
                            st.caption(f"Category: {item['category']}")
                        
                        with col2:
                            st.write(f"Qty: {item['quantity']}")
                        
                        with col3:
                            st.write(f"${item['price']:.2f}")
                        
                        with col4:
                            total_val = item['quantity'] * item['price']
                            st.write(f"${total_val:.2f}")
                        
                        st.divider()
            else:
                st.info("No recent items to display")
        
        else:
            # No items in inventory
            st.info("🎯 Your inventory is empty. Start by adding some items!")
            
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Add Your First Item", use_container_width=True, type="primary"):
                    st.session_state.page_redirect = "inventory"
                    st.rerun()
        
        # System status
        st.markdown("---")
        st.subheader("🔧 System Status")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.success("🟢 Database: Connected")
        
        with col2:
            user_count = len(list(db.collection('users').stream()))
            st.info(f"👥 Active Users: {user_count}")
        
        with col3:
            st.info(f"🕐 Last Updated: {datetime.now().strftime('%H:%M:%S')}")
    
    except Exception as e:
        st.error(f"Error loading dashboard: {e}")
        st.info("Please refresh the page or contact your administrator.")
