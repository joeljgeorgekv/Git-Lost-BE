#!/usr/bin/env python3
"""
Script to visualize the TripConsensusGraph as a Mermaid diagram.
This will generate both the Mermaid text and PNG image of the graph.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set up environment variables for the app
os.environ.setdefault("DATABASE_URL", "sqlite:///temp.db")
os.environ.setdefault("OPENAI_API_KEY", "dummy-key-for-graph-viz")

try:
    from app.langgraph.graphs.trip_consensus_graph import TripConsensusGraph
    
    def generate_mermaid_visualization():
        """Generate Mermaid diagram of the TripConsensusGraph."""
        print("🔄 Creating TripConsensusGraph...")
        
        # Create the graph
        consensus_graph = TripConsensusGraph()
        compiled_graph = consensus_graph.graph
        
        print("✅ Graph created successfully!")
        
        # Generate Mermaid text representation
        print("\n📝 Generating Mermaid diagram text...")
        try:
            mermaid_text = compiled_graph.get_graph().draw_mermaid()
            
            # Save Mermaid text to file
            mermaid_file = project_root / "trip_consensus_graph.mmd"
            with open(mermaid_file, "w") as f:
                f.write(mermaid_text)
            
            print(f"✅ Mermaid text saved to: {mermaid_file}")
            print("\n" + "="*60)
            print("MERMAID DIAGRAM TEXT:")
            print("="*60)
            print(mermaid_text)
            print("="*60)
            
        except Exception as e:
            print(f"❌ Error generating Mermaid text: {e}")
        
        # Generate PNG image (requires graphviz and pillow)
        print("\n🖼️  Generating PNG image...")
        try:
            png_data = compiled_graph.get_graph().draw_mermaid_png()
            
            # Save PNG to file
            png_file = project_root / "trip_consensus_graph.png"
            with open(png_file, "wb") as f:
                f.write(png_data)
            
            print(f"✅ PNG image saved to: {png_file}")
            
            # Try to display if in Jupyter/IPython
            try:
                from IPython.display import Image, display
                display(Image(png_data))
                print("📊 Image displayed above!")
            except ImportError:
                print("💡 To view the image, open: trip_consensus_graph.png")
                print("   Or install IPython to display inline: pip install ipython")
                
        except Exception as e:
            print(f"❌ Error generating PNG: {e}")
            print("💡 Make sure you have graphviz installed: brew install graphviz")
            print("💡 And pillow: pip install pillow")
        
        # Print graph statistics
        print(f"\n📊 Graph Statistics:")
        graph_dict = compiled_graph.get_graph().to_dict()
        nodes = graph_dict.get("nodes", [])
        edges = graph_dict.get("edges", [])
        
        print(f"   • Nodes: {len(nodes)}")
        print(f"   • Edges: {len(edges)}")
        print(f"   • Node Names: {[node['id'] for node in nodes]}")
        
        return mermaid_text, png_file
    
    if __name__ == "__main__":
        print("🚀 TripConsensusGraph Visualization Generator")
        print("=" * 50)
        
        try:
            mermaid_text, png_file = generate_mermaid_visualization()
            
            print(f"\n🎉 Visualization complete!")
            print(f"   📄 Mermaid file: trip_consensus_graph.mmd")
            print(f"   🖼️  PNG file: {png_file}")
            print(f"\n💡 You can:")
            print(f"   • Copy the Mermaid text to https://mermaid.live/ for online editing")
            print(f"   • Open the PNG file in any image viewer")
            print(f"   • Use the .mmd file in Mermaid-compatible editors")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()

except ImportError as e:
    print(f"❌ Import error: {e}")
    print("💡 Make sure you're running this from the project root directory")
    print("💡 And that all dependencies are installed: poetry install")
