import streamlit as st
from firebase_config import get_db
from firebase_admin import firestore  # Add this import
import pandas as pd

def app():
    st.title("📦 Inventory Management")
    
    db = get_db()
    if not db:
        st.error("Database connection failed")
        return
    
    # Tabs for different inventory operations
    tab1, tab2, tab3 = st.tabs(["View Inventory", "Add Item", "Update Item"])
    
    with tab1:
        st.subheader("Current Inventory")
        
        try:
            # Get all inventory items
            items = []
            docs = db.collection('inventory').stream()
            
            for doc in docs:
                item = doc.to_dict()
                item['id'] = doc.id
                items.append(item)
            
            if items:
                df = pd.DataFrame(items)
                st.dataframe(df, use_container_width=True)
                
                # Add delete functionality
                st.subheader("Delete Item")
                if items:
                    item_names = [f"{item['name']} (ID: {item['id']})" for item in items]
                    selected_item = st.selectbox("Select item to delete:", [""] + item_names)
                    
                    if selected_item and st.button("🗑️ Delete Item", type="secondary"):
                        item_id = selected_item.split("ID: ")[1].rstrip(")")
                        try:
                            db.collection('inventory').document(item_id).delete()
                            st.success("Item deleted successfully!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Error deleting item: {e}")
            else:
                st.info("No items in inventory yet.")
                
        except Exception as e:
            st.error(f"Error loading inventory: {e}")
    
    with tab2:
        st.subheader("Add New Item")
        
        with st.form("add_item_form"):
            name = st.text_input("Item Name")
            category = st.selectbox("Category", ["Electronics", "Clothing", "Food", "Books", "Other"])
            quantity = st.number_input("Quantity", min_value=0, value=0)
            price = st.number_input("Price per Unit", min_value=0.0, value=0.0, format="%.2f")
            description = st.text_area("Description")
            supplier = st.text_input("Supplier (Optional)")
            
            if st.form_submit_button("Add Item"):
                if name and quantity >= 0 and price >= 0:
                    try:
                        item_data = {
                            'name': name,
                            'category': category,
                            'quantity': quantity,
                            'price': price,
                            'description': description,
                            'supplier': supplier,
                            'created_by': st.session_state.user['username'],
                            'created_at': firestore.SERVER_TIMESTAMP,
                            'last_updated': firestore.SERVER_TIMESTAMP
                        }
                        
                        db.collection('inventory').add(item_data)
                        st.success(f"Item '{name}' added successfully!")
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"Error adding item: {e}")
                else:
                    st.error("Please fill in all required fields")
    
    with tab3:
        st.subheader("Update Item")
        
        try:
            # Get all items for selection
            items = []
            docs = db.collection('inventory').stream()
            
            for doc in docs:
                item = doc.to_dict()
                item['id'] = doc.id
                items.append(item)
            
            if items:
                # Select item to update
                item_options = {f"{item['name']} (Qty: {item['quantity']})": item for item in items}
                selected_item_name = st.selectbox("Select item to update:", [""] + list(item_options.keys()))
                
                if selected_item_name:
                    selected_item = item_options[selected_item_name]
                    
                    with st.form("update_item_form"):
                        st.write(f"Updating: **{selected_item['name']}**")
                        
                        new_name = st.text_input("Item Name", value=selected_item['name'])
                        new_category = st.selectbox("Category", 
                                                  ["Electronics", "Clothing", "Food", "Books", "Other"],
                                                  index=["Electronics", "Clothing", "Food", "Books", "Other"].index(selected_item.get('category', 'Other')))
                        new_quantity = st.number_input("Quantity", min_value=0, value=selected_item['quantity'])
                        new_price = st.number_input("Price per Unit", min_value=0.0, value=selected_item['price'], format="%.2f")
                        new_description = st.text_area("Description", value=selected_item.get('description', ''))
                        new_supplier = st.text_input("Supplier", value=selected_item.get('supplier', ''))
                        
                        if st.form_submit_button("Update Item"):
                            try:
                                updated_data = {
                                    'name': new_name,
                                    'category': new_category,
                                    'quantity': new_quantity,
                                    'price': new_price,
                                    'description': new_description,
                                    'supplier': new_supplier,
                                    'last_updated': firestore.SERVER_TIMESTAMP,
                                    'updated_by': st.session_state.user['username']
                                }
                                
                                db.collection('inventory').document(selected_item['id']).update(updated_data)
                                st.success(f"Item '{new_name}' updated successfully!")
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error updating item: {e}")
            else:
                st.info("No items available to update.")
                
        except Exception as e:
            st.error(f"Error loading items for update: {e}")
