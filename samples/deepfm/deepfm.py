import hugectr
from mpi4py import MPI
solver = hugectr.CreateSolver(max_eval_batches = 300,
                              batchsize_eval = 16384,
                              batchsize = 16384,
                              lr = 0.001,
                              vvgpu = [[0]],
                              repeat_dataset = True)
reader = hugectr.DataReaderParams(data_reader_type = hugectr.DataReaderType_t.Norm,
                                  source = ["./criteo_data/file_list.txt"],
                                  eval_source = "./criteo_data/file_list_test.txt",
                                  check_type = hugectr.Check_t.Sum)
optimizer = hugectr.CreateOptimizer(optimizer_type = hugectr.Optimizer_t.Adam,
                                    update_type = hugectr.Update_t.Global,
                                    beta1 = 0.9,
                                    beta2 = 0.999,
                                    epsilon = 0.0000001)
model = hugectr.Model(solver, reader, optimizer)
model.add(hugectr.Input(label_dim = 1, label_name = "label",
                        dense_dim = 13, dense_name = "dense",
                        data_reader_sparse_param_array = 
                        [hugectr.DataReaderSparseParam("data1", 2, False, 26)]))
model.add(hugectr.SparseEmbedding(embedding_type = hugectr.Embedding_t.DistributedSlotSparseEmbeddingHash, 
                            workspace_size_per_gpu_in_mb = 61,
                            embedding_vec_size = 11,
                            combiner = "sum",
                            sparse_embedding_name = "sparse_embedding1",
                            bottom_name = "data1",
                            optimizer = optimizer))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Reshape,
                            bottom_names = ["sparse_embedding1"],
                            top_names = ["reshape1"],
                            leading_dim=11))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Slice,
                            bottom_names = ["reshape1"],
                            top_names = ["slice11", "slice12"],
                            ranges=[(0,10),(10,11)]))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Reshape,
                            bottom_names = ["slice11"],
                            top_names = ["reshape2"],
                            leading_dim=260))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Reshape,
                            bottom_names = ["slice12"],
                            top_names = ["reshape3"],
                            leading_dim=26))                            
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.WeightMultiply,
                            bottom_names = ["dense"],
                            top_names = ["weight_multiply1"],
                            weight_dims= [13,10]))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.WeightMultiply,
                            bottom_names = ["dense"],
                            top_names = ["weight_multiply2"],
                            weight_dims= [13,1]))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Concat,
                            bottom_names = ["reshape2","weight_multiply1"],
                            top_names = ["concat1"]))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.InnerProduct,
                            bottom_names = ["concat1"],
                            top_names = ["fc1"],
                            num_output=400))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.ReLU,
                            bottom_names = ["fc1"],
                            top_names = ["relu1"]))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Dropout,
                            bottom_names = ["relu1"],
                            top_names = ["dropout1"],
                            dropout_rate=0.5))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.InnerProduct,
                            bottom_names = ["dropout1"],
                            top_names = ["fc2"],
                            num_output=400))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.ReLU,
                            bottom_names = ["fc2"],
                            top_names = ["relu2"]))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Dropout,
                            bottom_names = ["relu2"],
                            top_names = ["dropout2"],
                            dropout_rate=0.5))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.InnerProduct,
                            bottom_names = ["dropout2"],
                            top_names = ["fc3"],
                            num_output=400))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.ReLU,
                            bottom_names = ["fc3"],
                            top_names = ["relu3"]))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Dropout,
                            bottom_names = ["relu3"],
                            top_names = ["dropout3"],
                            dropout_rate=0.5))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.InnerProduct,
                            bottom_names = ["dropout3"],
                            top_names = ["fc4"],
                            num_output=1))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.FmOrder2,
                            bottom_names = ["concat1"],
                            top_names = ["fmorder2"],
                            out_dim=10))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.ReduceSum,
                            bottom_names = ["fmorder2"],
                            top_names = ["reducesum1"],
                            axis=1))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Concat,
                            bottom_names = ["reshape3","weight_multiply2"],
                            top_names = ["concat2"]))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.ReduceSum,
                            bottom_names = ["concat2"],
                            top_names = ["reducesum2"],
                            axis=1))
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.Add,
                            bottom_names = ["fc4", "reducesum1", "reducesum2"],
                            top_names = ["add"]))                                                                                                        
model.add(hugectr.DenseLayer(layer_type = hugectr.Layer_t.BinaryCrossEntropyLoss,
                            bottom_names = ["add", "label"],
                            top_names = ["loss"]))
model.compile()
model.summary()
model.fit(max_iter = 2300, display = 200, eval_interval = 1000, snapshot = 1000000, snapshot_prefix = "deepfm")

