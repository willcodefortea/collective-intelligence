from math import sqrt
import random

from PIL import Image, ImageDraw

from ci.distance import pearson, tanimoto
from ci.bi_tree import BiNode

def read_file(stream):
    """Parse a stream and build a friendly set of data"""
    lines = [line for line in stream]

    # First line is the column titles
    col_names = lines[0].strip().split('\t')[1:]
    rownames = []
    data = []

    for line in lines[1:]:
        chunks = line.split('\t')
        rownames.append(chunks[0])
        data.append([float(x) for x in chunks[1:]])

    return rownames, col_names, data

def hierarchical_clusters(rows, distance=pearson):
    """Convert a set of data to """
    distances = {}

    # Clusters are initially just the rows
    clusters = [BiNode(row, id=i) for i, row in enumerate(rows)]

    while len(clusters) > 1:
        lowest_pair = (0, 1)

        # Default the closest to the first two items
        closest = distance(clusters[0].vector, clusters[1].vector)

        for i in range(len(clusters)):
            for j in range(i+1, len(clusters)):
                # Check the distances
                key = (id(clusters[i]), id(clusters[j]))
                if key not in distances:
                    distances[key] = distance(clusters[i].vector, clusters[j].vector)

                if distances[key] < closest:
                    closest = distances[key]
                    lowest_pair = (i, j)

        # Merge our closets vectors and create new cluster
        cluster1 = clusters[lowest_pair[0]]
        cluster2 = clusters[lowest_pair[1]]
        vec1 = cluster1.vector
        vec2 = cluster2.vector
        merge_vector = [(vec1[i] + vec2[i]) / 2.0 for i in range(len(vec1))]

        new_cluster = BiNode(merge_vector, left=cluster1, right=cluster2,
                                distance=closest)

        # Prune the cluster list.
        del clusters[lowest_pair[1]]
        del clusters[lowest_pair[0]]
        clusters.append(new_cluster)

    return clusters[0]

def k_means_clustering(rows, distance=pearson, k=4):
    """Apply K-Means clustering to a data set"""
    # Find the ranges for each point
    ranges = []
    for i in range(len(rows)):
        row_min = min(row[i] for row in rows)
        row_max = max(row[i] for row in rows)
        ranges.append((row_min, row_max))

    # Create k randomly placed centroids
    clusters = [[] for _ in range(k)]
    for j in range(k):
        for i in range(len(rows)):
            clusters[j].append(random.random() * (ranges[i][1] - ranges[i][0]) + ranges[i][0])

    last_matches = None
    for t in range(100):
        print "Iteration: %d" % t
        best_matches = [[] for _ in range(k)]

        for j in range(len(rows)):
            row = rows[j]
            best_match = 0
            for i in range(k):
                d = distance(clusters[i], row)
                if d < distance(clusters[best_match], row):
                    best_match = i
            best_matches[best_match].append(j)

        # If the results are the same then we've done!
        if best_matches == last_matches:
            break
        else:
            last_matches = best_matches

        # Move the centroids to the average of their members
        for i in range(k):
            averages = [0.0, ] * len(rows[0])
            if len(best_matches[i]) > 0:
                for row_id in best_matches[i]:
                    for m in range(len(rows[row_id])):
                        averages[m] += rows[row_id][m]
                for j in range(len(averages)):
                    averages[j] /= len(best_matches[i])
                clusters[i] = averages

    return best_matches

def draw_dendrogram(node, labels, filename='nodes.jpg'):
    """Output a Dendrogram for a given node"""
    height = node.height * 20
    depth = node.depth
    width = 1200

    # Width is constant, so scale distances
    scaling = float(width - 150) / depth

    image = Image.new('RGB', (width, height), (255, 255, 255))
    draw = ImageDraw.Draw(image)

    draw.line((0, height/2, 10, height / 2), fill=(255,0 ,0))

    draw_node(draw, node, 10, (height/2), scaling, labels)
    image.save(filename, 'JPEG')

def draw_node(draw, node, x, y, scaling, labels):
    if node.is_leaf:
        # Just draw the label
        draw.text((x+5, y-7), labels[node.id], (0, 0, 0))
    else:
        h_left = node.left.height if node.left else 0
        h_right = node.right.height if node.right else 0

        h_left *= 20
        h_right *= 20

        top = y - (h_left + h_right) / 2
        bottom = y + (h_left + h_right) / 2

        line_length = node.distance * scaling
        # Draw a vertical line from this node to children
        draw.line((x, top + h_left / 2, x, bottom - h_right / 2), fill=(255, 0, 0))
        # Horizontal line to the left item
        draw.line((x, top + h_left / 2, x + line_length, top + h_left / 2), fill=(255, 0, 0))
        # Horizontal line to the right item
        draw.line((x, bottom - h_right / 2, x + line_length, bottom - h_right / 2), fill=(255, 0, 0))

        # Draw the left and right nodes
        if node.left:
            draw_node(draw, node.left, x + line_length, top + h_left / 2, scaling, labels)

        if node.right:
            draw_node(draw, node.right, x + line_length, bottom - h_right / 2, scaling, labels)

def rotate_matrix(data):
    """Flip rows and columns of a data set"""
    new_data = []
    for i in range(len(data[0])):
        new_row = [data[j][i] for j in range(len(data))]
        new_data.append(new_row)
    return new_data

if __name__ == '__main__':
    with open('blogdata.txt', 'rb') as fin:
        blog_names, words, data = read_file(fin)

    # cluster = hierarchical_clusters(rows=data)

    # # Uncomment to print the tree to console
    # # BiNode.print_cluster(cluster, labels=blog_names)
    # draw_dendrogram(cluster, labels=blog_names, filename='blogs.jpeg')

    # rotated_data = rotate_matrix(data)
    # rotated_clusters = hierarchical_clusters(rows=rotated_data)
    # draw_dendrogram(rotated_clusters, labels=words, filename='words.jpg')

    # # k_cluster = k_means_clustering(rows=data, k=10)
    # # print [blog_names[r] for r in k_cluster[0]]

    # with open('zebo.txt', 'rb') as fin:
    #     wants, people, data = read_file(fin)

    # cluster = hierarchical_clusters(data, distance=tanimoto)
    # draw_dendrogram(cluster, wants, filename='zebo.jpg')
